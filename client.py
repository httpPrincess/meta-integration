from facade import get_facade
from time import sleep
import logging

def print_instance_status(f):
# check instance status:
  for instance_id, instance in f.get_all_instances(1).iteritems():
      desc = f.get_instance(instance_id, 1)
      logging.info('%s --> %s' ,instance_id, desc['status'])


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
sleep(15)
logging.info('Starting tests')

logging.info('Getting types')
f = get_facade()
f.get_types()
assert len(f.get_types())>0

logging.info('Checking instances creation')
for type_name in f.get_types():
    res = f.create_instance(type_name, 1)
    assert res is not None
    
res = f.get_all_instances(1)
assert len(res)>0

logging.info('Instances status')
for i in range(1,10):
  print_instance_status(f)
  sleep(5)

logging.info('Test killing')  
for instance_id, instance in f.get_all_instances(1).iteritems():
  logging.info('Killing %s', instance_id)
  f.delete_instance(instance_id, 1)

sleep(5)
res = f.get_all_instances(1)
assert len(res)==0
