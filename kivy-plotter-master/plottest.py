
V = []
I = []
status = 'V'
val = ""
flag = True



plotData = "V2.2I2.4V3I3V4I4V5I5V6I6V7I7E"
corrupt = False

for i in range(1,len(plotData)):
    if(plotData[i] == 'V' or plotData[i] == 'I'):
        if (plotData[i] == status):
            if(status == 'V'):
                print("a")
            else:
                if(val.replace('.','',1).isdigit()):
                    flag = False
                    status = 'I'
                    if(len(I) < len(V)):
                        I.append(float(val))
                else:
                    corrupt = True
                    if(len(V) > len((I))):
                        V.pop()
        else:
            corrupt = False
            if(plotData[i] == 'V'):
                if(val.replace('.','',1).isdigit()):
                    if(flag is False):
                        flag = True
                        status = 'V'
                    else:
                        status = 'V'
                        if(corrupt ):
                            corrupt = False
                        else:
                            I.append(float(val))
                else:
                    if(len(V) > len((I))):
                        V.pop()
                    status = 'V'
            else:
                if(val.replace('.','',1).isdigit()):
                    status = 'I'
                    V.append(float(val))
                    #corrupt = False
                else:
                    corrupt = True
                    status = 'I'
        val = ""
    elif(plotData[i] == 'E'):
        if(val.replace('.','',1).isdigit() and len(I) < len(V)):
            I.append(float(val))
    else:
        val = val + plotData[i]

print(V,I )
