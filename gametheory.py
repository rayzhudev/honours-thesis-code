import sys
import time
import pprint

from web3 import Web3
from solcx import compile_source

def compile_source_file(file_path):
    with open(file_path, 'r') as f:
        source = f.read()

    return compile_source(source)

class GT_Contract:

    def __init__(self, smart_contract_path, ip_address):
        self.gas_limit = 3000000
        self.w3 = Web3(Web3.HTTPProvider(ip_address))
        self.w3.eth.defaultAccount = self.w3.eth.accounts[0]
        if not self.w3.isConnected():
            print("Can't connect to EVM")
            raise ConnectionError
        self.w3.geth.personal.unlock_account(self.w3.eth.accounts[0], "WelcomeToSirius")
        compiled_sol = compile_source_file(smart_contract_path)
        contract_id, contract_interface = compiled_sol.popitem()
        abi = contract_interface['abi']
        bytecode = contract_interface['bin']
        self.Contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
        receipt = self.deploy_contract(contract_interface)
        address = receipt.contractAddress
        self.gametheory_contract = self.w3.eth.contract(address=address, abi=abi)
        print(f'Deployed {contract_id} to: {address}')
        super().__init__()

    #returns tx receipt
    def deploy_contract(self, contract_interface):
        tx_hash = self.Contract.constructor().transact()
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        return tx_receipt

    #returns account address
    def make_account(self, passphrase):
        return self.w3.geth.personal.new_account(passphrase)

    #returns list of addresses
    def make_multiple_accounts(self, number):
        addresses = []
        for i in range(number):
            addresses.append(self.make_account(f"account{i}"))
        return addresses

    #returns nothing
    def set_account(self, address, passphrase):
        self.w3.eth.defaultAccount = address
        self.w3.geth.personal.unlock_account(address, passphrase)
        return

    #Smart contract functions

    def default_tx(self):
        return {'gas': self.gas_limit, 'from': self.w3.eth.defaultAccount}

    #returns tx receipt
    def mint(self, address, amount):
        tx_hash = self.gametheory_contract.functions.mint(address, amount).transact({'gas': self.gas_limit, 'from': self.w3.eth.defaultAccount})
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        return tx_receipt

    #returns own balance
    def get_self_balance(self):
        return self.gametheory_contract.functions.getBalance().call()

    #returns balance
    def get_balance(self, address):
       return self.gametheory_contract.functions.participants(address).call()

    #returns insurance held by account
    def get_insurance_holdings(self):
        return self.gametheory_contract.functions.getInsuranceHoldings().call()

    #returns the insurance record at the index
    def get_insurance(self, idx):
        return self.gametheory_contract.functions.insuranceLedger(idx).call()

    #returns the size of the committee
    def get_committee_size(self):
        return self.gametheory_contract.functions.getCommitteeSize().call()

    #return tx_receipt
    def join_committee(self):
        tx = {'value': self.w3.toWei(1, 'ether'), 'gas': self.gas_limit}
        tx_hash = self.gametheory_contract.functions.joinCommittee().transact(tx)
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        return tx_receipt

    #return tx_receipt
    def leave_committee(self):
        tx_hash = self.gametheory_contract.functions.leaveCommittee().transact()
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        return tx_receipt

    #return tx_receipt
    def send_transaction(self, receiver, amount, fee, reward):
        tx_hash = self.gametheory_contract.functions.sendTransaction(receiver, amount, fee, reward).transact()
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        return tx_receipt

    #return tx_receipt
    def forfeit_insurance(self, id):
        tx_hash = self.gametheory_contract.functions.forfeitInsurance(id).transact()
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        return tx_receipt
    
    #return tx_receipt
    def defect(self):
        tx_hash = self.gametheory_contract.functions.defect().transact(self.default_tx())
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        return tx_receipt
    
    def leave_byzantine_coalition(self):
        tx_hash = self.gametheory_contract.functions.leaveByzantineCoalition().transact(self.default_tx())
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        return tx_receipt

    def get_coalition_size(self):
        return self.gametheory_contract.functions.getByzantineCoalitionSize().call()

    ### Start of custom functions

    #returns total insurance held by sender
    def get_total_insurance_value(self):
        holdings = self.get_insurance_holdings()
        total = 0
        for _, i in enumerate(holdings):
            total += self.gametheory_contract.insuranceLedger(i).call()
        return total
    
    #returns nothing
    def forfeit_all_insurance(self):
        holdings = self.get_insurance_holdings()
        for _, i in enumerate(holdings):
            self.forfeit_insurance(i)
        return

