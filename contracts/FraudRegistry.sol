// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FraudRegistry {
    enum RecordStatus { Flagged, UnderReview, ResolvedSafe, ConfirmedFraud }

    struct FraudRecord {
        uint256 amount;
        string result;
        string senderName;
        string receiverName;
        uint256 timestamp;
        RecordStatus status;
    }

    address public owner;
    mapping(address => bool) public authorizedNodes;
    FraudRecord[] public transactions;

    event FraudLogged(
        uint256 indexed index,
        uint256 amount,
        string result,
        string senderName,
        string receiverName,
        uint256 timestamp,
        uint8 status
    );

    event StatusUpdated(
        uint256 indexed index,
        uint8 status,
        uint256 timestamp
    );

    event NodeAuthorized(address indexed node);
    event NodeRevoked(address indexed node);

    modifier onlyOwner() {
        require(msg.sender == owner, "Caller is not the owner");
        _;
    }

    modifier onlyAuthorized() {
        require(msg.sender == owner || authorizedNodes[msg.sender], "Caller is not authorized");
        _;
    }

    constructor() {
        owner = msg.sender;
        authorizedNodes[msg.sender] = true;
        emit NodeAuthorized(msg.sender);
    }

    function authorizeNode(address node) public onlyOwner {
        authorizedNodes[node] = true;
        emit NodeAuthorized(node);
    }

    function revokeNode(address node) public onlyOwner {
        authorizedNodes[node] = false;
        emit NodeRevoked(node);
    }

    function storeTransaction(
        uint256 _amount,
        string memory _result,
        string memory _sender,
        string memory _receiver
    ) public onlyAuthorized {
        transactions.push(
            FraudRecord({
                amount: _amount,
                result: _result,
                senderName: _sender,
                receiverName: _receiver,
                timestamp: block.timestamp,
                status: RecordStatus.Flagged
            })
        );

        emit FraudLogged(
            transactions.length - 1,
            _amount,
            _result,
            _sender,
            _receiver,
            block.timestamp,
            uint8(RecordStatus.Flagged)
        );
    }

    function updateTransactionStatus(uint256 index, uint8 _status) public onlyAuthorized {
        require(index < transactions.length, "Index out of bounds");
        require(_status <= uint8(RecordStatus.ConfirmedFraud), "Invalid status code");
        
        transactions[index].status = RecordStatus(_status);
        emit StatusUpdated(index, _status, block.timestamp);
    }

    function getTransactionCount() public view returns (uint256) {
        return transactions.length;
    }

    function getTransaction(uint256 index)
        public
        view
        returns (
            uint256 amount,
            string memory result,
            string memory senderName,
            string memory receiverName,
            uint256 timestamp,
            uint8 status
        )
    {
        require(index < transactions.length, "Index out of bounds");
        FraudRecord storage record = transactions[index];
        return (
            record.amount,
            record.result,
            record.senderName,
            record.receiverName,
            record.timestamp,
            uint8(record.status)
        );
    }
}
