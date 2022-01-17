from pyclbr import Function
from typing import List,Tuple
import requests
import datetime
from configure import PROMETEO_KEY
from utils import providers_format,provider_info
from utils import formating_account,formating_credit_cards,formating_account_movements

URL = 'https://banking.sandbox.prometeoapi.com/'


def get_providers()->List:
    """Get the providers info from the API"""
    r=requests.get(URL+'provider/',headers={'X-API-KEY':PROMETEO_KEY})
    providers=[]
    if r.status_code==200:
        providers = r.json()['providers']
        providers.append({"code":"All","country":'WW','name':'All providers'})
        providers= providers_format(providers)
    return providers

#Get the providers data
providers = get_providers()
providers_codes,providers_names = provider_info(providers)
providers= [p['name']+' '+p['country'] for p in providers]

class User:
    def __init__(self,**kwargs)->None:
        self.api_key ={'X-API-Key':kwargs.get('key',PROMETEO_KEY)}
        self.user_data = {'All':{}}
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
    def operation_in_all_providers(self,operation:Function,*args, **kwargs)->List:
        result= []
        for k in self.user_data.keys():
            if k is not 'All':
                result.append(providers_names[k])
                result.extend(operation(k))
        return result

    def not_found(self,provider:str)->str:
        return f'Sorry, that operation for {provider} is not allowed'

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
