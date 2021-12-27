from scripts.helpful_scripts import get_account
from brownie import interface, config, network


def get_weth():
    """
    Mint WETH by deposit ETH
    """
    account = get_account()
    active_network = network.show_active()
    # ABI
    weth = interface.IWeth(config["networks"][active_network]["weth_token"])
    tx = weth.deposit({"from": account, "value": 0.001 * 10 ** 18})
    print("Recieve 0.1 WETH")
    return tx


def main():
    get_weth()
