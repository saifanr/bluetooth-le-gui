
V = []
I = []
status = 'V'
val = ""
flag = True

def isfloat(val):
    try:
        float(val)
        return True
    except ValueError:
        return False

plotData = plotData = "V-1.000I-15.028V-.993I-14.909V-.986I-14.908V-.980I-14.908V-.973I-14.104V-.966I-1.44E"
corrupt = False

for i in range(1,len(plotData)):
    if(plotData[i] == 'V' or plotData[i] == 'I'):
        if (plotData[i] == status):
            if(status == 'V'):
                print("a")
            else:
                if(isfloat(val)):
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
                if(isfloat(val)):
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
                if(isfloat(val)):
                    status = 'I'
                    V.append(float(val))
                    #corrupt = False
                else:
                    corrupt = True
                    status = 'I'
        val = ""
    elif(plotData[i] == 'E'):
        if(isfloat(val) and len(I) < len(V)):
            I.append(float(val))
    else:
        val = val + plotData[i]

print(V,I )





