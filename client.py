from facade import get_facade
from time import sleep

def print_instance_status(f):
# check instance status:
  for instance_id, instance in f.get_all_instances(1).iteritems():
      desc = f.get_instance(instance_id, 1)
      print '%s --> %s' % (instance_id, desc['status'])

# get types:
f = get_facade()
f.get_types()

# create instances:
for type_name in f.get_types():
    f.create_instance(type_name, 1)

for i in range(1,10):
  print_instance_status(f)
  sleep(5)
  
for instance_id, instance in f.get_all_instances(1).iteritems():
  print 'Killing %s' % instance_id
  f.delete_instance(instance_id, 1)

