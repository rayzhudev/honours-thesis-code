from contract_client import Byzantine, Client, Committee, Honest, Rational
import gametheory
import sys, time, signal
from time import sleep
from web3 import Web3
#from matplotlib.animation import FuncAnimation
#from matplotlib import pyplot as plt
import random
import math

client_nodes = []
committee_nodes = []
byzantine_nodes = []
NUMBER_OF_CLIENT_NODES = 5
NUMBER_OF_HONEST_NODES = 5
NUMBER_OF_RATIONAL_NODES = 0
RATIONAL_RISK = 0.5
RATIONAL_RISK_2 = 0.2
NUMBER_OF_BYZANTINE_NODES = 0
NUMBER_OF_COMMITTEE_NODES = NUMBER_OF_HONEST_NODES + NUMBER_OF_RATIONAL_NODES + NUMBER_OF_BYZANTINE_NODES
SIMULATION_LENGTH = 100
INITIAL_BALANCE_VALUE = 100000

def setup(contract):
    accounts = contract.make_multiple_accounts(NUMBER_OF_COMMITTEE_NODES+NUMBER_OF_CLIENT_NODES)
    for i, address in enumerate(accounts):
        tx = {'value': w3.toWei(1000, 'ether'), 'to': address, 'from': w3.eth.accounts[0], 'gas': 30000000}
        tx_hash = w3.geth.personal.send_transaction(tx, "WelcomeToSirius")
        w3.eth.waitForTransactionReceipt(tx_hash)
        contract.mint(address, INITIAL_BALANCE_VALUE)
        # check_balance(i, 10000)

    for i in range(NUMBER_OF_CLIENT_NODES):
        new_node = Client(contract, accounts[i], f"account{i}")
        client_nodes.append(new_node)

    comm_count = 0
    for i in range(NUMBER_OF_CLIENT_NODES, NUMBER_OF_CLIENT_NODES+NUMBER_OF_COMMITTEE_NODES):
        new_node = 0
        if comm_count < NUMBER_OF_HONEST_NODES:
            new_node = Honest(contract, accounts[i], f"account{i}")
        elif comm_count >= NUMBER_OF_HONEST_NODES and comm_count < NUMBER_OF_HONEST_NODES + NUMBER_OF_RATIONAL_NODES:
            # new_node = Rational(contract, accounts[i], f"account{i}", random.uniform(0.1, 0.9))
            if comm_count % 2 == 0:
                new_node = Rational(contract, accounts[i], f"account{i}", RATIONAL_RISK)
            else:
                new_node = Rational(contract, accounts[i], f"account{i}", RATIONAL_RISK_2)
        elif comm_count >= NUMBER_OF_HONEST_NODES + NUMBER_OF_RATIONAL_NODES and comm_count < NUMBER_OF_HONEST_NODES + NUMBER_OF_RATIONAL_NODES + NUMBER_OF_BYZANTINE_NODES:
            new_node = Byzantine(contract, accounts[i], f"account{i}")
        new_node.start()
        committee_nodes.append(new_node)
        comm_count += 1
    assert(len(committee_nodes)==NUMBER_OF_COMMITTEE_NODES), "wrong amount of committee nodes"

def run(file):
    txs_sent = []
    revealed_fork = 100
    compromised_txs = {}
    unrefunded_txs = {}
    turns_without_refunds = 0
    successful_refunds = 0
    unsuccessful_refunds = 0
    tx_ticker = 0
    timestep = 0
    while timestep < SIMULATION_LENGTH:
        # select node to send a transaction
        curr_node_idx = random.randrange(0, NUMBER_OF_CLIENT_NODES)
        curr_node = client_nodes[curr_node_idx]
        target_idx = random.randrange(0, NUMBER_OF_CLIENT_NODES)
        while target_idx == curr_node_idx:
            target_idx = random.randrange(0, NUMBER_OF_CLIENT_NODES)
        target = client_nodes[target_idx].address
        #amount = math.floor(random.uniform(0.01, 0.05) * curr_node.balance) # change to send different amount of money between nodes
        amount = 2000
        fee = 100 # change to give committee different amount of fees
        #reward = math.floor(random.uniform(0.05, 0.15) * amount) # change to give different reward to receiver
        reward = 200

        #evaluate revealed forks
        com_size, byz_size = committee_nodes[0].get_comm_byz()
        txs_to_del = []
        for tx in compromised_txs:
            roll = random.randint(1,2)

            if roll == 1 and not byz_size/com_size > 2/3:
                revealed_fork = timestep
                txs_to_del.append(tx)
        for tx in txs_to_del:
            del compromised_txs[tx]
        
        # forfeit all available insurance holdings under expected value constraints
        turns_without_refunds += 1
        for node in client_nodes:
            t, arr = node.forfeit_insurance(timestep, txs_sent, revealed_fork)
            for item in arr:
                if item in compromised_txs:
                    unsuccessful_refunds += 1
                else:
                    successful_refunds += 1
                del unrefunded_txs[item]
                turns_without_refunds = 0
        # attempt a fork within committee nodes
        for node in committee_nodes:
            if isinstance(node, Rational):
                node.evaluate_committee(turns_without_refunds)
                node.start_fork(amount, com_size, byz_size)
            if isinstance(node, Honest):
                node.evaluate_committee(turns_without_refunds)
        com_size, byz_size = committee_nodes[0].get_comm_byz()

        for i, node in enumerate(client_nodes):
            print(f"Client {i} balance: {node.balance}")
        print(f"Sending transaction to {target_idx} from {curr_node_idx}, amount: {amount}, fee: {fee}, reward: {reward}")
        try:
            if curr_node.send_transaction(target, amount, fee, reward):
                tx_ticker += 1
                if byz_size/com_size > 1/3:
                    compromised_txs[tx_ticker] = timestep
                txs_sent.append(amount)
                unrefunded_txs[tx_ticker] = amount
            else:
                print("Transaction failed, insufficient balance")
        except:
            print("Transaction failed, insufficient balance")
        timestep += 1
        print(f"Successful txs: {tx_ticker}, Successful refunds: {successful_refunds}, Locked up currency: {sum(unrefunded_txs.values())}, # of byzantine nodes: {byz_size}/{com_size}, # of compromised txs: {len(compromised_txs)}, Unsuccessful refunded: {unsuccessful_refunds}")
        file.write(f"{tx_ticker},{successful_refunds},{sum(unrefunded_txs.values())},{byz_size},{com_size},{len(compromised_txs)},{unsuccessful_refunds}\n")#
    file.close()

#handle exit
def signal_handler(sig, frame):
    print("Final balances")
    for i, node in enumerate(client_nodes):
        node.force_forfeit_insurance()
        print(f"Client {i} balance: {node.balance}")
    for i, node in enumerate(committee_nodes):
        node.end()
        print(f"Committee {i} balance: {node.balance}")
    sys.exit(0)

if __name__ == "__main__":
    file = open("results.out", "w")
    #signal.signal(signal.SIGINT, signal_handler)
    if not len(sys.argv) == 3:
        print("Smart contract file and ip address required")
        sys.exit()
    w3 = Web3(Web3.HTTPProvider(sys.argv[2]))
    w3.eth.defaultAccount = w3.eth.accounts[0]
    w3.geth.personal.unlock_account(w3.eth.accounts[0], "WelcomeToSirius")
    GT_Contract = gametheory.GT_Contract(sys.argv[1], sys.argv[2])
    setup(GT_Contract)
    file.write(f"Honest: {NUMBER_OF_HONEST_NODES} Rational: {NUMBER_OF_RATIONAL_NODES} Byzantine: {NUMBER_OF_BYZANTINE_NODES}\n")
    run(file)
    # ani = FuncAnimation(plt.gcf(), run, 200)
    # plt.tight_layout()
    # plt.show()