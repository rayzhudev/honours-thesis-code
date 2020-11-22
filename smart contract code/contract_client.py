import gametheory
import sys
from web3 import Web3
from web3.logs import STRICT, IGNORE, DISCARD, WARN
from math import ceil, floor

class Client():

    def __init__(self, contract, address, passphrase): 
        self.gametheory = contract
        self.address = address
        self.passphrase = passphrase
        self.gametheory.set_account(self.address, self.passphrase)
        self.balance = self.gametheory.get_self_balance()

    def forfeit_insurance(self, tx_ticker, txs_sent, most_recent_fork):
        self.gametheory.set_account(self.address, self.passphrase)
        insurance_holdings = self.gametheory.get_insurance_holdings()
        total_forfeited = 0
        txs_forfeited = []
        for holding in insurance_holdings:
            if holding == 0:
                continue
            record = self.gametheory.get_insurance(holding)
            fork_chance = pow(50, (-(tx_ticker - holding)/8) + 1) * 0.01 * max(10-most_recent_fork, 1)
            expected_val = fork_chance * txs_sent[holding-1]
            if record[1] >= expected_val:
                self.gametheory.forfeit_insurance(holding)
                total_forfeited += 1
                self.balance += record[1]
                txs_forfeited.append(holding)
        return total_forfeited, txs_forfeited

    def send_transaction(self, address, amount, fee, reward):
        self.gametheory.set_account(self.address, self.passphrase)
        self.balance = self.gametheory.get_self_balance()
        if self.balance < amount + fee + reward:
            return False
        receipt = self.gametheory.send_transaction(address, amount, fee, reward)
        # processed_receipt = self.gametheory.events.myEvent().processReceipt(receipt, errors=IGNORE)
        # print("processed receipt ",end='')
        # print(processed_receipt)
        return True

    def force_forfeit_insurance(self):
        self.gametheory.set_account(self.address, self.passphrase)
        self.gametheory.forfeit_all_insurance()

class Committee():

    def __init__(self, contract, address, passphrase): 
        self.gametheory = contract
        self.address = address
        self.passphrase = passphrase
        self.in_committee = False
    
    def start(self):
        self.gametheory.set_account(self.address, self.passphrase)
        self.gametheory.join_committee()
        self.in_committee = True

    def end(self):
        self.gametheory.leave_committee()
        self.in_committee = False

    def get_comm_byz(self):
        com_size = self.gametheory.get_committee_size()
        byz_size = self.gametheory.get_coalition_size()
        return com_size, byz_size

class Honest(Committee):

    def __init__(self, contract, address, passphrase):
        super().__init__(contract, address, passphrase)
    
    def evaluate_committee(self, ticks):
        self.gametheory.set_account(self.address, self.passphrase)
        if ticks >= 10 and self.in_committee:
            self.gametheory.leave_committee()
            self.in_committee = False
        elif ticks < 10 and not self.in_committee:
            self.gametheory.join_committee()
            self.in_committee = True

class Rational(Honest):

    def __init__(self, contract, address, passphrase, risk):
        super().__init__(contract, address, passphrase)
        self.risk = risk
        self.defected = False

    def start_fork(self, amount, com_size, byz_size):
        if com_size == 0:
            return
        self.gametheory.set_account(self.address, self.passphrase)
        fork_success_chance = (byz_size + (floor(self.risk*(com_size-byz_size))))/ceil(com_size*(2/3))
        #print(f"{fork_success_chance}% chance of fork"")
        expected_return = fork_success_chance * amount/(byz_size+1)
        expected_loss = (1-fork_success_chance) * amount/(byz_size+1)
        if expected_return > expected_loss and not self.defected:
            self.defected = True
            self.gametheory.defect()
            return True
        elif expected_return <= expected_loss and self.defected:
            self.defected = False
            self.gametheory.leave_byzantine_coalition()
            return False

    def evaluate_committee(self, ticks):
        self.gametheory.set_account(self.address, self.passphrase)
        if ticks >= 10 and self.in_committee:
            if self.defected:
                self.gametheory.leave_byzantine_coalition()
                self.defected = False
            self.gametheory.leave_committee()
            self.in_committee = False
        elif ticks < 10 and not self.in_committee:
            self.gametheory.join_committee()
            self.in_committee = True

class Byzantine(Committee):

    def __init__(self, contract, address, passphrase):
        super().__init__(contract, address, passphrase)

    def start(self):
        super().start()
        self.gametheory.defect()

def check_balance(index, amount):
    val = GT_Contract.get_balance(accounts[index])
    print(f"Account {index} balance: {val}")
    assert (val == amount), "Balance is incorrect"

def eth_balance(address):
    return w3.fromWei(w3.eth.getBalance(address), 'ether')

if __name__ == "__main__":
    if not len(sys.argv) == 3:
        print("Smart contract file and ip address required")
        sys.exit()
    w3 = Web3(Web3.HTTPProvider(sys.argv[2]))
    w3.eth.defaultAccount = w3.eth.accounts[0]
    w3.geth.personal.unlock_account(w3.eth.accounts[0], "WelcomeToSirius")
    print(f"Eth balance: {eth_balance(w3.eth.accounts[0])}")
    GT_Contract = gametheory.GT_Contract(sys.argv[1], sys.argv[2])
    accounts = GT_Contract.make_multiple_accounts(3)
    clients = []
    for i, address in enumerate(accounts):
        tx = {'value': w3.toWei(5, 'ether'), 'to': address, 'from': w3.eth.accounts[0], 'gas': 30000000}
        tx_hash = w3.geth.personal.send_transaction(tx, "WelcomeToSirius")
        w3.eth.waitForTransactionReceipt(tx_hash)
        GT_Contract.mint(address, 10000)
        check_balance(i, 10000)
        clients.append(Client(GT_Contract, address, f"account{i}"))
    print(f"{len(accounts)} accounts made and minted with balance 10000")
    GT_Contract.set_account(accounts[1], "account1")
    GT_Contract.join_committee()
    print("Account 1 joined committee")
    clients[0].send_transaction(accounts[2], 1300, 100, 100)
    check_balance(0, 8500)
    check_balance(2, 11300)
    clients[2].forfeit_insurance(0)
    clients[0].send_transaction(accounts[2], 1300, 100, 100)
    clients[2].forfeit_insurance(0)
    GT_Contract.set_account(accounts[2], "account2")
    GT_Contract.forfeit_insurance(1)
    clients[2].forfeit_insurance(0)
    GT_Contract.forfeit_insurance(2)
    clients[2].forfeit_insurance(0)

    # GT_Contract.set_account(accounts[0], "account0")
    # GT_Contract.send_transaction(accounts[2], 1300, 100, 100)
    # print("Account 0 sent tx to Account 2 with values 1300, 100, 100")
    # check_balance(0, 8500)
    # check_balance(2, 11300)
    # GT_Contract.set_account(accounts[2], "account2")
    # holdings = GT_Contract.get_insurance_holdings()
    # assert (holdings == [1]), "Insurance holdings wrong"
    # GT_Contract.forfeit_all_insurance()
    # print("Account 2 forfeits insurance")
    # GT_Contract.set_account(accounts[1], "account1")
    # GT_Contract.leave_committee()
    # print("Account 1 leaves committee")
    # check_balance(1, 10100)
    # check_balance(2, 11400)
    # print("Test completed: SUCCESS")
