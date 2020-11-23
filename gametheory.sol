// Ray's smart contract which models the game theory scenario of PoS.

pragma solidity >=0.7.0 <0.8.0;

contract GameTheory {

    address public minter;

    uint public committeeLength;
    uint public coalitionLength;
    uint public depositValue = 1 ether; // minimum 1 ETH to join committee
    uint public depositMultiplier = 1; // gives 1 GameTheory token per wei for deposit
    uint public maxCommitteeSize = 100;
    uint public standardFee = 100; // fee per transaction
    uint txID; // id for each transaction

    struct InsuranceRecord {
        address[] guarantors;
        uint[] value;
        address insuree;
        uint reward;
        bool compromised;
    }

    struct User {
        uint balance;
        uint[] insuranceHoldings;
    }

    struct CommitteeMember {
        bool exists;
        uint deposit;
        uint feeRewards;
        address member;
        uint byzantineIndex;
    }

    address[] public committee;
    address[] public byzantineCoalition;
    mapping(address => CommitteeMember) public committeeMembers;
    mapping(address => User) public participants;
    mapping(uint => InsuranceRecord) public insuranceLedger;

    // Event for transactions
    event Sent(address from, address to, uint amount);

    // Event for joining/leaving committee
    event CommitteeUpdate(address member, bool join);

    // Receive Ether
    event Received(address, uint);

    // Event for forfeiting insurance for a transaction
    event InsuranceForfeited(uint);

    // Event for number of byzantines in committee
    event ByzantineCoalitionSize(uint);

    receive() external payable {
        emit Received(msg.sender, msg.value);
    }

    constructor() public {
        minter = msg.sender;
        committeeLength = 0;
        coalitionLength = 0;
        byzantineCoalition.push(msg.sender);
        txID = 1;
    }

    function getBalance() public view returns(uint) {
        return participants[msg.sender].balance;
    }

    function getInsuranceHoldings() public view returns(uint[] memory) {
        return participants[msg.sender].insuranceHoldings;
    }

    function getCommitteeSize() public view returns(uint) {
        return committeeLength;
    }

    function getByzantineCoalitionSize() public view returns(uint) {
        return coalitionLength;
    }

    function joinCommittee() public payable {
        require(msg.value >= depositValue);
        require(committeeLength < maxCommitteeSize);
        require(committeeMembers[msg.sender].exists == false);
        require(committeeMembers[msg.sender].deposit == 0);
        committeeMembers[msg.sender] = CommitteeMember({exists: true, deposit: depositValue*depositMultiplier, feeRewards: 0, member: msg.sender, byzantineIndex: 0});
        committee.push(msg.sender);
        committeeLength++;
        emit CommitteeUpdate(msg.sender, true);
    }

    function leaveCommittee() public {
        require(committeeMembers[msg.sender].exists == true);
        // require(committeeMembers[msg.sender].deposit == depositValue*depositMultiplier);
        participants[msg.sender].balance += committeeMembers[msg.sender].feeRewards; // add fees to balance
        // remove from array
        for (uint i = 0; i < committee.length; i++) { 
            if (committee[i] == msg.sender) {
                delete committee[i];
                break;
            }
            assert(i != committee.length - 1);
        }
        delete committeeMembers[msg.sender]; // remove from mapping
        committeeLength--;
        msg.sender.transfer(depositValue);
        emit CommitteeUpdate(msg.sender, false);
    }

    function mint(address receiver, uint amount) public {
        require(msg.sender == minter);
        require(amount < 1e60);
    
        participants[receiver].balance += amount;
    }

    // Sends an amount of existing coins
    // from any caller to an address
    function sendTransaction(address receiver, uint amount, uint fee, uint reward) public {
        require(amount > 0);
        require((amount + fee + reward) <= participants[msg.sender].balance); // total cost to send transaction is amount + fee + reward
        require(committeeLength > 0);
        require(fee >= standardFee);

        uint depositShare = amount / committeeLength;
        uint depositDifference = amount - (depositShare*committeeLength);
        uint feePayable = fee / committeeLength;
        uint feeDifference = fee - (feePayable*committeeLength);
        uint amountCovered = 0;
        uint committeeIndex = 0;

        address[] memory temp_guarantors = new address[](committeeLength);
        uint[] memory temp_value = new uint[](committeeLength);
        for (uint i = 0; i < committee.length; i++) {
            if (committee[i] == address(0)) {
                continue;
            }
            require(committeeMembers[committee[i]].deposit > depositShare); // simple solution to prevent deposit unable to be filled
            committeeMembers[committee[i]].deposit -= depositShare;
            amountCovered += depositShare;
            committeeMembers[committee[i]].feeRewards += feePayable;
            temp_guarantors[committeeIndex] = committee[i];
            temp_value[committeeIndex] = depositShare;
            committeeIndex++;
        }
        committeeIndex = 0;
        assert(depositDifference < committeeLength); // deposit difference should never be more than size of committee
        for (uint j = 0; j < depositDifference; j++) {
            if (committee[j] == address(0)) {
                depositDifference++;
                continue;
            } else {
                committeeMembers[committee[j]].deposit--;
                temp_value[committeeIndex]++;
                amountCovered++;
                committeeIndex++;
            }
        }
        assert(feeDifference < committeeLength); // fee difference should never be more than size of committee
        for (uint k = 0; k < feeDifference; k++) {
            if (committee[k] == address(0)) {
                feeDifference++;
                continue;
            } else {
                committeeMembers[committee[k]].feeRewards++;
            }
        }

        insuranceLedger[txID] = InsuranceRecord({guarantors: temp_guarantors, value: temp_value, insuree: receiver, reward: reward, compromised: (coalitionLength > committeeLength/3)});
        participants[receiver].insuranceHoldings.push(txID);
        txID++;
        participants[receiver].balance += amount;
        participants[msg.sender].balance -= amount + fee + reward;
        emit Sent(msg.sender, receiver, amount);
    }

    function forfeitInsurance(uint id) public {
        require(insuranceLedger[id].insuree == msg.sender);
        uint insuranceHoldingsIndex;
        for (uint i = 0; i < participants[msg.sender].insuranceHoldings.length; i++) {
            if (participants[msg.sender].insuranceHoldings[i] == id) {
                insuranceHoldingsIndex = i;
                break;
            }
        }
        require(insuranceHoldingsIndex >= 0);
        require(participants[msg.sender].insuranceHoldings[insuranceHoldingsIndex] == id);
        assert(insuranceLedger[id].guarantors.length == insuranceLedger[id].value.length); // check that same amount of guarantors as values    
        // if (insuranceLedger[id].compromised) { // do something else if there has been a fork
        //     for (uint i = 0; i < insuranceLedger[id].guarantors.length; i++) {
        //         committeeMembers[insuranceLedger[id].guarantors[i]].deposit += insuranceLedger[id].value[i];
        //     }
        //     uint total_value = 0;
        //     for (uint i = 0; i < insuranceLedger[id].value.length; i++) {
        //         participants[msg.sender].balance -= insuranceLedger[id].value[i];
        //         total_value += insuranceLedger[id].value[i];
        //     }
        //     for (uint i = 0; i < byzantineCoalition.length; i++) {
        //         participants[byzantineCoalition[i]].balance += total_value/byzantineCoalition.length;
        //     }
        //     delete participants[msg.sender].insuranceHoldings[insuranceHoldingsIndex];
        // } else {
        for (uint i = 0; i < insuranceLedger[id].guarantors.length; i++) {
            committeeMembers[insuranceLedger[id].guarantors[i]].deposit += insuranceLedger[id].value[i];
        }
        participants[msg.sender].balance += insuranceLedger[id].reward;
        delete participants[msg.sender].insuranceHoldings[insuranceHoldingsIndex];
        // }
    }

    function defect() public {
        require(committeeMembers[msg.sender].exists == true);
        committeeMembers[msg.sender].byzantineIndex = byzantineCoalition.length;
        byzantineCoalition.push(msg.sender);
        coalitionLength++;
        emit ByzantineCoalitionSize(coalitionLength);
    }

    function leaveByzantineCoalition() public {
        require(committeeMembers[msg.sender].exists == true);
        if (committeeMembers[msg.sender].byzantineIndex > 0) {
            delete byzantineCoalition[committeeMembers[msg.sender].byzantineIndex];
            coalitionLength--;
        }
    }

}