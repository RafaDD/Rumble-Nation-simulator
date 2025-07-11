import glob
import pandas as pd
import os

def find_best(stage, n_player):
    filepaths = glob.glob(f'./model_offline/{stage}-{n_player}/*/args.csv')

    dfs = []
    for fp in filepaths:
        df = pd.read_csv(fp)

        model_dir = os.path.basename(os.path.dirname(fp))
        df['model_dir'] = model_dir

        dfs.append(df)

    all_args_df = pd.concat(dfs, ignore_index=True)

    sorted_df = all_args_df.sort_values(by='test_loss', ascending=True).reset_index(drop=True)

    return sorted_df

if __name__ == '__main__':
    print(find_best(0, 2))
