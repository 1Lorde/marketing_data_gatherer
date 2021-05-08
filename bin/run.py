import pathlib
import sys

if __name__ == '__main__':
    print(str(pathlib.Path(__file__).parent.parent.absolute()))
    sys.path.append(str(pathlib.Path(__file__).parent.parent.absolute()))

    from bin.main import main

    main()
