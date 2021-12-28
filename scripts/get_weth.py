from scripts.helpful_scripts import get_account
from brownie import interface, config, network


def get_weth(amount: float, account=None):
    """
    Mint WETH by deposit ETH
    """
    if not account:
        account = get_account()
    active_network = network.show_active()
    # ABI
    weth = interface.IWeth(config["networks"][active_network]["weth_token"])
    tx = weth.deposit({"from": account, "value": amount})
    print(f"Recieve {amount} WETH")
    return tx


def main():
    get_weth()
