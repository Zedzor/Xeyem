from django.http import Http404
from coinaddrvalidator import validate
from . import bitcoininvestigate 
from . import ethereuminvestigate


def __get_module(address: str) -> dict:
    
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
      token_dict = __get_module(address)
  except Http404:
      raise
  else:
    module = token_dict['module'] 
    shared_func = getattr(module, 'get_common_info')
    shared_info = shared_func(address)
    if shared_info is None:
        raise Http404("Address not found")
    # Use returned module and execute requested functionalities
    for item in funcs:
        func = getattr(token_dict['module'], item, None)
        if func is not None:
            shared_info,result = func(shared_info)
            results.update(result)
    func = getattr(token_dict['module'], 'store_results', None)
    if func is not None:
        func(shared_info, results)
    return results
