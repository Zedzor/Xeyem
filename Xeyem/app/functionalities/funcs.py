from django.http import Http404
from coinaddrvalidator import validate
import bitcoininvestigate 
import ethereuminvestigate


SHARED_API_FUNCS = {'balance', 'fst_lst_transaction', 'transactions', 'transactions_stats'}

def _get_module(address: str) -> dict:
    
    # validate if addr is btc eth or neither and select module 
    if validate('btc', address).valid:
        return {
            'module': bitcoininvestigate
            }
    elif validate('eth', address).valid:
        return {
            'module': ethereuminvestigate
        }
    else:
        raise Http404("Address not found")
    
   
def execute_search(address: str, funcs: set) -> dict:
  results = {} # return value
  
  # Check if addr exists and get module to use
  try:
      token_dict = _get_module(address)
  except Http404:
      raise
  else:
      # Check if a function that uses the shared endpoint is requested
      if len(SHARED_API_FUNCS.intersection(funcs)) > 0:
          shared_func = getattr(token_dict['module'], 'get_common_info')
          shared_info = shared_func(address)

      # Use returned module and execute requested functionalities
      for item in funcs:
          func = getattr(token_dict['module'], item, None)
          if func is not None:
              if item in SHARED_API_FUNCS:
                  results.update(func(shared_info))
              else:
                  results.update(func(address))
      return results
