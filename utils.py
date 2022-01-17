
from typing import List,Tuple

COUNTRIES = {
    'MX':'🇲🇽',
    'PE':'🇵🇪',
    'CL':'🇨🇱',
    'UY':'🇺🇾',
    'BR':'🇧🇷',
    'EC':'🇪🇨',
    'CO':'🇨🇴',
    'PA':'🇵🇦',
    'AR':'🇦🇷',
    'WW':'🌎',
}

def providers_format(providers:List)->List:
    """Change the country name to an emoji flag"""
    format_list= []
    for i in providers:
        i['country']=COUNTRIES[i['country']]
        format_list.append(i)
    return format_list
        
def provider_info(providers:List)->Tuple[List,List]:
    """Generate a list of dict with a format for providers info"""
    providers_name_code = {f'{p["name"]} {p["country"]}':p['code'] for p in providers}
    providers_code_name = {p['code']:f'{p["name"]} {p["country"]}' for p in providers}
    return providers_name_code,providers_code_name


def formating_account(accounts:List)->List:
    """Format the accounts info to a string multiline"""
    text= []
    for i in accounts:
        if(i):
            name = i.get('name','')
            number = i['number']
            currency= i['currency']
            balance = i['balance']
            line_account=f"<b>Name: </b>{name}\n<b>Number: </b>{number}\n<b>Balance: </b>{balance} {currency}\n"
            text.append(line_account)
        else:
            text.append('You dont have an account in this provider yet')
    return text

def formating_credit_cards(credit_cards:List)->List:
    """Format the credit cards info to a string multiline"""
    text= []
    for card in credit_cards:
        if(card):
            name = card['name']
            number = card['number']
            close_date= card['close_date']
            due_date = card['due_date']
            local_balance = card['balance_local']
            dollar_balance = card['balance_dollar']
            line_account=f"<b>Name: </b>{name}\n<b>Number: </b>{number}\n<b>Balance local: </b>{local_balance}\n<b>Balance dolar: </b> {dollar_balance} $\n<b>Close date: </b>{close_date}\n<b>Due date: </b>{due_date}"
            text.append(line_account)
        else:
            text.append('You dont have any credit card in this provider yet')
    return text

def formating_account_movements(account_movements:List,currency:str)->List:
    """Format the account movements into a a string multiline"""
    text = []
    total_credit,total_debit=0,0
    for movement in account_movements:
        if(movement):
            id_m = movement['id']
            date = movement['date']
            detail = movement['detail']
            debit = movement['debit']
            credit = movement['credit']
            if(debit):
                total_debit+=debit
                amount = f"<b>Debit :</b>{debit} {currency}"
            else:
                total_credit+=credit
                amount = f"<b>Credit :</b>{credit} {currency}"
            line_movement = f"<b>Id: </b>{id_m}\n<b>Date: </b>{date}\n<b>Details: </b>{detail}\n{amount}"
            text.append(line_movement)
        else:
            text.append('You dont have movements on this date range')
    text.append(f'<b>Total debit: </b>{total_debit:.2f} {currency}\n<b>Total credit: </b>{total_credit:.2f} {currency}')
    return text