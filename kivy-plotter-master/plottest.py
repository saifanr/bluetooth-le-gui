plotData = ['V','1','.','3','I','3','.','3','5','V','1','.','3','I','3','.','5','V','1','.','3','I','3','.']
V = []
I = []
status = 'V'
val = ""
for i in range(1,len(plotData[:-1])):
  if(plotData[i] == 'V'):
    status = 'V'
    I.append(val)
    val = ""
  elif(plotData[i] == 'I'):
    status = 'V'
    V.append(val)
    val = ""
  else:
    val = val + plotData[i]
