from scripts.helpful_scripts import get_account
from scripts.get_weth import get_weth
from brownie import network, config, interface
from web3 import Web3


ACTICE_NETWORK = network.show_active()
# 0.1
AMOUNT = Web3.toWei(0.1, "ether")


def get_lending_pool():
    lending_pool_address_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][ACTICE_NETWORK]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_address_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool
    # ABI
    # Address


def approve_erc20(amount, spender, erc20_address, account):
    print("Approveing ERC20 token...")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved")
    return tx


def get_borrowable_data(lending_pool, account):
    # https://docs.aave.com/developers/the-core-protocol/lendingpool#getuseraccountdata
    (
        total_collatateral_wei,
        total_dept_wei,
        available_borrow_wei,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)
    available_borrow_eth = Web3.fromWei(available_borrow_wei, "ether")
    total_collatateral_eth = Web3.fromWei(total_collatateral_wei, "ether")
    total_dept_eth = Web3.fromWei(total_dept_wei, "ether")

    print(f"You have {total_collatateral_eth} worth of ETH deposited.")
    print(f"You have {total_dept_eth} worth of ETH borrowed.")
    print(f"You can borrow  {available_borrow_eth} worth of ETH.")

    return (float(worth) for worth in [available_borrow_wei, total_dept_wei])


def get_asset_price(price_feed_address):
    # ABI
    # Address
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]  # Index 1 for price
    converted_latest_price = Web3.fromWei(latest_price, "ether")
    print(f"The DAI/ETH price is {converted_latest_price}")
    return float(latest_price)


def repay_all(amount, lending_pool, account):
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool,
        config["networks"][ACTICE_NETWORK]["dai_token"],
        account,
    )
    # https://docs.aave.com/developers/the-core-protocol/lendingpool#repay
    # function repay(address asset, uint256 amount, uint256 rateMode, address onBehalfOf)
    repay_tx = lending_pool.repay(
        config["networks"][ACTICE_NETWORK]["dai_token"],
        amount,
        1,
        account.address,
        {"from": account},
    )
    repay_tx.wait(1)
    print("Repay!")
    return repay_tx


def main():
    account = get_account()

    erc20_address = config["networks"][ACTICE_NETWORK]["weth_token"]

    get_weth(AMOUNT, account)
    lending_pool = get_lending_pool()
    # Approve sending out ERC20 tokens
    print("Lending pool")
    print(lending_pool.address)
    approve_erc20(AMOUNT, lending_pool.address, erc20_address, account)

    print("Depositing")
    # https://docs.aave.com/developers/the-core-protocol/lendingpool#deposit
    # deposit()
    # function deposit(address asset, uint256 amount, address onBehalfOf, uint16 referralCode)
    tx = lending_pool.deposit(
        erc20_address,
        AMOUNT,
        account.address,
        0,
        {"from": account},
    )
    tx.wait(1)
    print("Deposited")

    available_borrow_eth, total_dept_eth = get_borrowable_data(lending_pool, account)
    print("Let's borrow!")
    # DAI in terms of ETH
    dai_eth_price = get_asset_price(
        config["networks"][ACTICE_NETWORK]["dai_eth_price_feed"]
    )
    amount_dai_to_borrow = (1 / dai_eth_price) * (available_borrow_eth * 0.95)
    # borrowable eth -> borrowable dai * 95%
    print(f"We are going to boroow {amount_dai_to_borrow} DAI")
    # https://docs.aave.com/developers/the-core-protocol/lendingpool#borrow
    dai_address = config["networks"][ACTICE_NETWORK]["dai_token"]
    # function borrow(address asset, uint256 amount, uint256 interestRateMode, uint16 referralCode, address onBehalfOf)
    borrow_tx = lending_pool.borrow(
        dai_address,  # asset
        Web3.toWei(amount_dai_to_borrow, "ether"),  # asset
        1,  # interestRateMode
        0,  # referralCode
        account.address,  # onBehalfOf
        {"from": account},
    )
    borrow_tx.wait(1)
    print("We borrowed some DAI!")
    get_borrowable_data(lending_pool, account)

    repay_all((available_borrow_eth * 0.95) ** 1e18, lending_pool, account)

    print("You just deposited, borrowed and repayed with Aave, Brownie and Chainlink")
