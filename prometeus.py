from typing import List,Tuple
import requests
import datetime
from configure import PROMETEO_KEY
URL = 'https://banking.sandbox.prometeoapi.com/'

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
}

def providers_format(providers:List)->List:
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

def get_providers()->List:
    """Get the providers info from the API"""
    r=requests.get(URL+'provider/',headers={'X-API-KEY':PROMETEO_KEY})
    providers=[]
    if r.status_code==200:
        providers= providers_format(r.json()['providers'])
    return providers

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

class User:
    def __init__(self,**kwargs)->None:
        self.api_key ={'X-API-Key':kwargs.get('key',PROMETEO_KEY)}
        self.user_data = {}
        self.__set_operations_dictionary()

    def set_user_data(self,**kwargs)->None:
        username=kwargs.get('username')
        provider=kwargs.get('provider')
        password=kwargs.get('password')
        if provider not in self.user_data:
            self.user_data[provider]={
                'data':{
                'username':username,
                'password':password,
                'provider':provider,
                }
            }
    def __set_operations_dictionary(self)->None:
        self.operations={
            'account':self.get_accounts,
            'credit_cards':self.get_credit_cards,
            'account_movements':self.get_account_movements,
        }
    def check_session_time(self)->bool:
        actual_time = datetime.datetime.now()
        if(((actual_time-self.time).total_seconds()/60)>5):
            print((actual_time-self.time).total_seconds()/60)
            return False
        return True        

    def login(self,provider='test')->bool:
        r = requests.post(URL+'login/',data=self.user_data[provider]['data'],headers=self.api_key)
        if r.status_code==200:
            self.user_data[provider]['key']=r.json()['key']
            #The session key is for the api-key or for each provider login?
            self.time = datetime.datetime.now()
            return True
        return False

    def wrapper_operation(self,operation:str,provider:str,*args, **kwargs)->List:
        if((self.check_session_time()) or (self.login(provider))):
            operation_function = self.operations.get(operation,self.not_found)
            if(provider is not 'All'):
                return operation_function(provider,*args, **kwargs)
            else:

                return self.operation_in_all_providers(operation_function,*args, **kwargs)
    def operation_in_all_providers(self,operation:str,*args, **kwargs)->List:
        results= []
        for k in self.user_data.keys():
            if k is not 'All':
                result = self.operations.get(operation,self.not_found)(k)
                results.append(result)
        return results

    def not_found(self,provider:str)->List:
        return [f'Sorry, that operation for {provider} is not allowed']

    def get_accounts(self,provider:str,*args, **kwargs)->List:
        r= requests.get(URL+'account/', params={'key':self.user_data[provider]['key']},headers=self.api_key)
        if r.status_code==200:
            accounts = r.json()['accounts']
            if not 'accounts' in self.user_data[provider]:
                self.user_data[provider]['accounts']={}
            for account in accounts:
                self.user_data[provider]['accounts'][account['name']]=account
            return formating_account(accounts)
        return [r.json()['message']]
            
    def get_credit_cards(self,provider:str)->str:
        r=requests.get(URL+'credit-card/',params={'key':self.user_data[provider]['key']},headers=self.api_key)
        if r.status_code==200:
            self.user_data[provider]['credit_cards']=r.json()['credit_cards']
            return formating_credit_cards(r.json()['credit_cards'])
        return [r.json()['message']]
    def get_account_movements(self,provider:str,*args, **kwargs)->List:
        account = kwargs.get('account','')
        date_start= kwargs.get('first_date','')
        date_end= kwargs.get('second_date','None')
        account_data = self.user_data[provider]['accounts'][account]
        key = self.user_data[provider]['key']
        r=requests.get(f"{URL}account/{account_data['number']}/movement/",params={'key':key,'currency':account_data['currency'],'date_start':date_start,'date_end':date_end,},headers=self.api_key)
        if r.status_code==200:
            return formating_account_movements(r.json()['movements'],account_data['currency'])
        return [r.json()['message']]
