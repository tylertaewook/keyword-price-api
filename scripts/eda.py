import pandas as pd


if __name__ == "__main__":
    # dummy script to use vscode's debug console
    dp = pd.read_csv("./dataprice.csv")
    df = dp.loc[:, ~dp.columns.str.contains("^Unnamed")]
    print("hi")
