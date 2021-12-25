from typing import List
import requests
import datetime
URL = 'https://banking.sandbox.prometeoapi.com/'
PROMETEO_KEY= 'Waiting for a smile from a sun child.'

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
        
def provider_info(providers:List)->(List):
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

def formating_account(accounts:List)->str:
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

def formating_credit_cards(credit_cards:List)->str:
    """Format the credit cards info to a string multiline"""
    text= []
    for i in credit_cards:
        if(i):
            name = i['name']
            number = i['number']
            close_date= i['close_date']
            due_date = i['due_date']
            local_balance = i['balance_local']
            dollar_balance = i['balance_dollar']
            line_account=f"<b>Name: </b>{name}\n<b>Number: </b>{number}\n<b>Balance local: </b>{local_balance}\n<b>Balance dolar: </b> {dollar_balance} $\n<b>Close date: </b>{close_date}\n<b>Due date: </b>{due_date}"
            text.append(line_account)
        else:
            text.append('You dont have any credit card in this provider yet')
    return text

class User:
    user_data = {}
    def __init__(self,**kwargs)->None:
        self.api_key ={'X-API-Key':kwargs.get('key',PROMETEO_KEY)}
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
        }
    def check_session_time(self)->bool:
        actual_time = datetime.datetime.now()
        if(((actual_time-self.time).total_seconds()/60)>5):
            print((actual_time-self.time).total_seconds())
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

    def wrapper_operation(self,operation:str,provider:str)->str:
        if((self.check_session_time()) or (self.login(provider))):
            operation_function = self.operations.get(operation,self.not_found)
            if(provider is not 'all'):
                return operation_function(provider)
            else:
                return self.operation_in_all_providers(operation_function)
    def operation_in_all_providers(self,operation:str)->str:
        results= []
        for k in self.user_data.keys():
            result = self.operations.get(operation,self.not_found)(k)
            results.append(result)
        return results

    def not_found(self,provider:str)->str:
        return f'Sorry, that operation for {provider} is not allowed'

    def get_accounts(self,provider:str)->str:
        r= requests.get(URL+'account/', params={'key':self.user_data[provider]['key']},headers=self.api_key)
        if r.status_code==200:
            return formating_account(r.json()['accounts'])
            
    def get_credit_cards(self,provider:str)->str:
        r=requests.get(URL+'credit-card/',params={'key':self.user_data[provider]['key']},headers=self.api_key)
        if r.status_code==200:
            return formating_credit_cards(r.json()['credit_cards'])
