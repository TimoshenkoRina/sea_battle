import ...

def print_welcome():


def main():

    print_welcome()

    while True:
        game = Game()
        game.setup()
        game.run()

        if stop:
            break

    print ('спасибо за игру')

if __name__ == '__main__':
    main()
