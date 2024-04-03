next = [None for _ in range(1000)]
prev = [None for _ in range(1000)]
intersection = []

inp = input('Enter edges: ').split(',')
for i in inp:
  n = [int(x) + 500 for x in i.split('>')]
  if prev[n[1]] != -1 and prev[n[1]] != None:
    intersection.append(n[1])
  next[n[0]] = n[1]
  prev[n[1]] = n[0]
  if prev[n[0]] == None:
    prev[n[0]] = -1
  if next[n[1]] == None:
    next[n[1]] = n[1]

if intersection == []:
  print('No intersection')
  exit(0)

intersection = list(set(intersection))
intersection.sort()

for i in intersection:
  cnt = 1
  if next[i] == i:
    print(f'Node({i - 500}, size={cnt})')
    continue
  cnt += 1
  path = [i]
  tmp = next[i]
  while next[tmp] != tmp and tmp not in path:
    cnt += 1
    path.append(tmp)
    tmp = next[tmp]
  if tmp in path:
    cnt -= 1
  print(f'Node({i - 500}, size={cnt})')

ans = []
print('Delete intersection then swap merge:')
for i in range(1000):
  if prev[i] == -1 or prev[i] in intersection:
    if next[i] == i:
      print(f'Node({i - 500}, size={cnt})')
      continue
    path = [i]
    tmp = next[i]
    while next[tmp] != tmp and tmp not in path:
      path.append(tmp)
      tmp = next[tmp]
    ans.append(path)

max_len = 0
for i in range(len(ans)):
  max_len = max(max_len, len(ans[i]))

s = ""
for j in range(max_len):
  for i in range(len(ans)):
    if j >= len(ans[i]):
      continue
    s += str(ans[i][j] - 500) + ' -> '

print(s[:-4])
