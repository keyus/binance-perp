import tools
import tg

    
def perp():
    # tools.tiker()
    # tools.klines()
    tools.read_klines()
    
def send_message():
    tg.run()
    
def main():
    perp()
    # send_message()

if __name__ == "__main__":
    main()