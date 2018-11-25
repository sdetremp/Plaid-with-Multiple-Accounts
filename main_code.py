from plaid import Client
import pandas as pd
import json
import datetime

from matplotlib import pyplot as plt
from matplotlib import style

style.use('dark_background')

BANK1 = 'THE ACCESS TOKEN FOR BANK ACCOUNT 1' #Insert the access token received from the public token assigned to each account
BANK2 = 'THE ACCESS TOKEN FOR BANK ACCOUNT 2'
TODAY = datetime.datetime.today()

with open('THE FILE LOCATION OF YOUR CREDENTIALS', 'r') as f:
    creds = json.load(f)
    client_id = creds['client_id']
    secret = creds['secret']
    public_key = creds['public_key']

client = Client(client_id=client_id,
                secret=secret,
                public_key=public_key,
                environment='development') #use development or production depending on the scale of your project


class BankInfo:
    """Initialize bank information"""
    def __init__(self, access_token):
        self.accounts = (client.Accounts.get(access_token))
        self.transactions = (client.Transactions.get(access_token,
                                                     start_date=str(TODAY.year - 1) + '-01-01',
                                                     end_date=str(TODAY)[:10])['transactions'])
        self.total_transactions = (client.Transactions.get(access_token,
                                                           start_date=str(TODAY.year - 1) + '-01-01',
                                                           end_date=str(TODAY)[:10])['total_transactions'])
        while len(self.transactions) < self.total_transactions:
            response = client.Transactions.get(access_token,
                                               start_date=str(TODAY.year - 1) + '-01-01',
                                               end_date=str(TODAY)[:10],
                                               offset=len(self.transactions))
            self.transactions.extend(response['transactions'])
        self.categories = (client.Categories.get())
        try:
            self.checking_account = self.accounts['accounts'][1]['balances']['current']
        except:
            self.checking_account = self.accounts['accounts'][0]['balances']['current']

        return

    def transaction_data(self):
        """Organize transaction data into pandas dataframe"""
        transaction_dict = {'Amount': [], 'Date': [], 'Name': [], 'Category1': [], 'Category2': []}
        for i in self.transactions:
            transaction_dict['Amount'].append(i['amount'])
            transaction_dict['Date'].append(i['date'])
            transaction_dict['Name'].append(i['name'])
            if i['category'] is not None and len(i['category']) > 1:
                transaction_dict['Category1'].append(i['category'][0])
                transaction_dict['Category2'].append(i['category'][1])
            elif i['category'] is not None:
                transaction_dict['Category1'].append(i['category'][0])
                transaction_dict['Category2'].append('')
            else:
                transaction_dict['Category1'].append('NA')
                transaction_dict['Category2'].append('')

        df = pd.DataFrame(transaction_dict, columns=['Date', 'Amount', 'Name', 'Category1', 'Category2'])
        df.set_index('Date', inplace=True)
        return df

bank1 = BankInfo(BANK1).transaction_data()
bank2 = BankInfo(BANK2).transaction_data()


def combine_dataframes(account1, account2):
    """Combine the dataframes from the various bank accounts - this is called in the subsequent routines"""
    combined = pd.concat([account1, account2])
    combined = combined.sort_index()
    start_date = input('Input Start Date (yyyy-mm-dd): ') #User chooses start date and end date
    end_date = input('Input End Date (yyyy-mm-dd): ')
    month = combined.loc[start_date:end_date]

    # Filter out line items that cross over between the 2 bank accounts such as transfers
    mask1 = month['Name'].str.contains('Transfer') == False

    filtered = month[mask1]
    return filtered, start_date, end_date


def calc_spend(account1, account2):
    """Summary spend for specific time period"""
    df, start_date, end_date = combine_dataframes(account1, account2)
    total_spend = df[df['Amount'] > 0]['Amount'].sum()
    total_earned = df[df['Amount'] < 0]['Amount'].sum() * -1
    net = df['Amount'].sum() * -1
    print(df)
    print('Total Spend: ${0:,.2f}\n'
          'Total Earned: ${1:,.2f}\n'
          'Net Gain/Loss: ${2:,.2f}\n'.format(total_spend, total_earned, net))
    return


def graph_running_balance(account1, account2):
    """Summary graph of running balance for specific time period"""
    df, start_date, end_date = combine_dataframes(account1, account2)
    df = df.groupby(df.index).sum()
    idx = pd.date_range(start_date, end_date)
    df.index = pd.DatetimeIndex(df.index)
    df = df.reindex(idx, fill_value=0)
    df = df * -1
    df['Total'] = [df['Amount'].iloc[x] + df['Amount'].iloc[0:x].sum() if x > 0 else df['Amount'].iloc[x]
                       for x in range(0, len(df['Amount']))]
    print(df, '\n')
    print('Current Net Worth: ${0:,.2f}'.format(df['Total'][-1]))
    df['Total'].plot(color='c')
    plt.title('Net Worth')
    plt.show()
    return


def graph_spend_per_month(account1, account2):
    df, start_date, end_date = combine_dataframes(account1, account2)
    start_date = str(df.index[0])
    df.index = pd.to_datetime(df.index)

    # Filter out line items from income so that you only capture spend
    mask1 = df['Name'].str.contains('Income') == False
    df = df[mask1]

    df = df.groupby(df.index.month)
    for key, item in df:
        print(key, '\n', df.get_group(key), '\n', '${0:,.2f}'.format(df.get_group(key)['Amount'].sum()), '\n\n')

    df = df['Amount'].sum()
    ax = df.plot.bar(color='c')
    ax.set_title('Spend by Category since ' + start_date)
    plt.ylabel('Spend in $')
    plt.xlabel('Month')
    ylabels = [format(label, ',.0f') for label in ax.get_yticks()]
    ax.set_yticklabels(ylabels)
    plt.xticks(rotation=0)

    rects = ax.patches
    for rect in rects:
        y_value = rect.get_height()
        x_value = rect.get_x() + rect.get_width() / 2
        space = 5
        va = 'bottom'
        if y_value < 0:
            space *= -1
            va = 'top'
        label = '${:,}'.format(int(y_value))

        plt.annotate(
            label,
            (x_value, y_value),
            xytext=(0, space),
            textcoords="offset points",
            ha='center',
            va=va)
    plt.show()
    return


def spend_by_category(account1, account2):
    """Summarize spend by category for specific time period"""
    df, start_date, end_date = combine_dataframes(account1, account2)
    start_date = str(df.index[0])

    # Filter out line items from income so that you only capture spend
    mask1 = df['Name'].str.contains('Income') == False
    df = df[mask1]

    df = df.groupby(['Category1'])
    for key, item in df:
        print(key, '\n', df.get_group(key), df.get_group(key)['Amount'].sum(), '\n\n')

    df = df['Amount'].sum()
    print(df, '\n')
    print('Total Spend: ${0:,.2f}'.format(df.sum()))

    ax = df.plot.bar(color='c')
    ax.set_title('Spend by Category since ' + start_date)
    ylabels = [format(label, ',.0f') for label in ax.get_yticks()]
    ax.set_yticklabels(ylabels)
    plt.xticks(rotation=30)

    rects = ax.patches
    for rect in rects:
        y_value = rect.get_height()
        x_value = rect.get_x() + rect.get_width() / 2
        space = 5
        va = 'bottom'
        if y_value < 0:
            space *= -1
            va = 'top'
        label = '${:,}'.format(int(y_value))

        plt.annotate(
            label,
            (x_value, y_value),
            xytext=(0, space),
            textcoords="offset points",
            ha='center',
            va=va)
    plt.show()
    return


if __name__ == '__main__':
    calc_spend(bank1, bank2)
