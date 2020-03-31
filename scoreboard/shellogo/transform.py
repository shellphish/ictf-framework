import os

lines = []
with open('orig.txt', 'r') as f:
  for line in f:
    lines.append(line)

new_lines = []
count = 0
for line in lines:
  new_line = []
  for c in line:
    if c != ' ':
      new_line.append('0')
    else:
      new_line.append('1')
  print ''.join(new_line)  
  new_lines.append(new_line)
  count += 1
print count

with open('shellphishlogo.js', 'w') as f:
  f.write('let logo = [')
  for line in new_lines:
    f.write('[')
    f.write(','.join(line))
    f.write('],')
  
  f.write('];')
  f.write('export default logo;')
