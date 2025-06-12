import utils.tools as utils
import utils.tg as tg_bot


    
def perp():
    # utils.tiker()
    utils.klines()
    utils.read_klines()
    
def send_message():
    tg_bot.run()
    
def main():
    send_message()
    # perp()

if __name__ == "__main__":
    main()