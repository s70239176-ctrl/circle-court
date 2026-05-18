// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IERC20 {
    function transferFrom(address from, address to, uint256 value) external returns (bool);
    function transfer(address to, uint256 value) external returns (bool);
}

contract CircleCourtEscrow {
    enum Status {
        Open,
        Funded,
        Resolved,
        Cancelled
    }

    struct Escrow {
        address buyer;
        address seller;
        address token;
        uint256 amount;
        Status status;
        string metadataUri;
    }

    address public owner;
    mapping(bytes32 => Escrow) public escrows;

    event EscrowCreated(bytes32 indexed escrowId, address indexed buyer, address indexed seller, uint256 amount, string metadataUri);
    event EscrowFunded(bytes32 indexed escrowId);
    event EscrowResolved(bytes32 indexed escrowId, uint256 sellerAmount, uint256 buyerRefund);

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function createEscrow(bytes32 escrowId, address buyer, address seller, address token, uint256 amount, string calldata metadataUri) external onlyOwner {
        require(escrows[escrowId].buyer == address(0), "exists");
        require(buyer != address(0) && seller != address(0), "bad parties");
        escrows[escrowId] = Escrow(buyer, seller, token, amount, Status.Open, metadataUri);
        emit EscrowCreated(escrowId, buyer, seller, amount, metadataUri);
    }

    function fund(bytes32 escrowId) external {
        Escrow storage escrow = escrows[escrowId];
        require(msg.sender == escrow.buyer, "not buyer");
        require(escrow.status == Status.Open, "not open");
        require(IERC20(escrow.token).transferFrom(msg.sender, address(this), escrow.amount), "transfer failed");
        escrow.status = Status.Funded;
        emit EscrowFunded(escrowId);
    }

    function resolve(bytes32 escrowId, uint16 sellerBasisPoints) external onlyOwner {
        require(sellerBasisPoints <= 10000, "bad split");
        Escrow storage escrow = escrows[escrowId];
        require(escrow.status == Status.Funded || escrow.status == Status.Open, "not resolvable");
        escrow.status = Status.Resolved;
        uint256 sellerAmount = (escrow.amount * sellerBasisPoints) / 10000;
        uint256 buyerRefund = escrow.amount - sellerAmount;
        if (sellerAmount > 0) require(IERC20(escrow.token).transfer(escrow.seller, sellerAmount), "seller transfer failed");
        if (buyerRefund > 0) require(IERC20(escrow.token).transfer(escrow.buyer, buyerRefund), "buyer transfer failed");
        emit EscrowResolved(escrowId, sellerAmount, buyerRefund);
    }
}
