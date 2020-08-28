import sys
from prettytable import PrettyTable

#reading file input from command line
fileData = open(sys.argv[1],'r')
fileData_= fileData.readlines()

transactionTable ={}
lockTable = {}
timeStamp = 0


#to display transaction table in output
def DisplayTransactiontable(transactionTable):
    transactionTableDisplay = PrettyTable()
    transactionIds = []
    transactionTS = []
    transStatus = []
    itemsList = []
    opsWaiting = []
    blockedby = []
    #adding each column elements to list
    for eachKey in transactionTable:
        transactionIds.append(eachKey)
        transactionTS.append(transactionTable[eachKey]['ts'])
        transStatus.append(transactionTable[eachKey]['transactionStatus'])
        if(transactionTable[eachKey]['transactionStatus']=='abort' or transactionTable[eachKey]['transactionStatus']=='committed'):
            blockedby.append("None")
            itemsList.append('')
            opsWaiting.append('')
        else:
            blockedby.append(transactionTable[eachKey]['blockedBy'])
            itemsList.append(transactionTable[eachKey]['ItemIds'])
            opsWaiting.append(transactionTable[eachKey]['waitingOps'])
    #column headers
    transactionT_column_names = ["Transaction Id","TimeStamp","Status", "Items Accessed", "Blocked By","Operations Waiting"]

    #adding column content under each header
    transactionTableDisplay.add_column(transactionT_column_names[0], transactionIds)
    transactionTableDisplay.add_column(transactionT_column_names[1], transactionTS) 
    transactionTableDisplay.add_column(transactionT_column_names[2], transStatus)  
    transactionTableDisplay.add_column(transactionT_column_names[3], itemsList)  
    transactionTableDisplay.add_column(transactionT_column_names[4], blockedby)
    transactionTableDisplay.add_column(transactionT_column_names[5], opsWaiting)

    return transactionTableDisplay

#to display lock table in output
def lockTableDisplay(lockTable):
    lockTableDisplay = PrettyTable()
    itemList = []
    lockMode = []
    holdingTranactionsList = []
    waitingTrans = []

    for eachItem in lockTable:
        if lockTable[eachItem]['lockState'] != 'unlocked':
            itemList.append(eachItem)
            lockMode.append(lockTable[eachItem]['lockState'])
            holdingTranactionsList.append(lockTable[eachItem]['holdingTids'])
            waitingTrans.append(lockTable[eachItem]['waitingTids'])

    lockTableColumnNames = ['Data Item','Lock Mode','Holding Tids','Waiting Tids']

    lockTableDisplay.add_column(lockTableColumnNames[0], itemList)
    lockTableDisplay.add_column(lockTableColumnNames[1], lockMode)
    lockTableDisplay.add_column(lockTableColumnNames[2], holdingTranactionsList)
    lockTableDisplay.add_column(lockTableColumnNames[3], waitingTrans)

    return lockTableDisplay

#to unlock items if transaction is committed or aborted
def unlock(item,transactionId):
    itemHoldingTids = lockTable[item]['holdingTids']
    waitingTids = lockTable[item]['waitingTids']
    tempWaitingTrans = []
    
    for eachTid in itemHoldingTids:
        #Remove current transaction from holdingTids list if it is aborted or committed
        if eachTid==transactionId and (transactionTable[eachTid]['transactionStatus']=="abort" or transactionTable[eachTid]['transactionStatus']=="committed"):
            lockTable[item]['holdingTids'].remove(eachTid)
            print(item+" unlocked from "+eachTid+" "+lockTable[item]['lockState']+" lock")
            if eachTid in waitingTids:
                #Removing aborted transaction from waiting transactions list
                lockTable[item]['waitingTids'].remove(eachTid)


    #if transaction holding list of item is empty, set lock state of item unlocked          
    if len(lockTable[item]['holdingTids'])==0:
        #print(item+"is unlocked")
        lockTable[item]['lockState'] = "unlocked"
    
    for eachT in waitingTids:
        tempWaitingTrans.append(eachT)
    
    #processing waiting operations
    if len(waitingTids)!=0:
        #first waiting operation is copied to currentWaitingTid
        currentWaitingTid = lockTable[item]['waitingTids'][0]
        for eachTrans in tempWaitingTrans:
            waitingOperations = []
            tempWaitOperationsList = []
            if transactionTable[eachTrans]['transactionStatus'] == "block" and lockTable[item]['waitingTids'][0] == eachTrans and transactionId in transactionTable[eachTrans]['blockedBy']:
                if lockTable[item]['lockState'] == "unlocked" or lockTable[item]['lockState'] == "read":
                    lockTable[item]['waitingTids'].remove(eachTrans)
                    print(eachTrans+" has resumed ")
                    transactionTable[eachTrans]['blockedBy'].remove(transactionId)
                    transactionTable[eachTrans]['transactionStatus'] = 'active'
                    waitingOperations = transactionTable[eachTrans]['waitingOps']
                    for eachOperation in waitingOperations:
                        tempWaitOperationsList.append(eachOperation)
                    for eachOp in tempWaitOperationsList:
                        displayFlag = 1
                        #operation should be removed from waiting Operations list
                        transactionTable[eachTrans]['waitingOps'].remove(eachOp)
                        print('executing '+eachOp)
                        execute(eachOp,displayFlag)

#Aborting transaction
def abort(transactionId):
    #transaction status set to abort
    transactionTable[transactionId]['transactionStatus'] = "abort"
    itemsList  = transactionTable[transactionId]['ItemIds']
    print("Items held by"+transactionId+":")
    #unlocking each item held by aborted transactions
    for item in itemsList:
        unlock(item,transactionId)

#blocking transaction
def blockTransaction(requestingTid,item,line):
    #status set as block and adding to waiting transaction list
    transactionTable[requestingTid]['transactionStatus'] = "block"
    lockTable[item]['waitingTids'].append(requestingTid)
    transactionTable[requestingTid]['waitingOps'].append(line)
    operationList = transactionTable[requestingTid]['waitingOps']
    return operationList


#wount wait algorithm to deal with conflict state
def woundWait(requestingTid,item,line):
    #comparing timestamps of holding transaction and requesting transaction, to resolve conflict
    requestingTs =  transactionTable[requestingTid]['ts']
    holdingTrans = ','.join(lockTable[item]['holdingTids'])  
    holdingOlderTransactions = []
    youngerholdingTids = []
    waitingOps = []
    for each_tid in lockTable[item]['holdingTids']:   #t2,t3
        holdingTs = transactionTable[each_tid]['ts']
        if(holdingTs>requestingTs):
            youngerholdingTids.append(each_tid)
        elif(holdingTs<requestingTs):
            holdingOlderTransactions.append(each_tid)
    #otherHoldingTrans islist of all holding transactions
    otherHoldingTrans = ','.join(youngerholdingTids+holdingOlderTransactions)

    print("Operation "+line+" "+item+" is locked by "+holdingTrans+", wound wait is checked comparing "+requestingTid+" timestamp with timestamp(s) of "+otherHoldingTrans)

    #if all holding transactions are younger than current transaction
    if(len(youngerholdingTids)>0 and len(holdingOlderTransactions)==0):
        for each_tid in youngerholdingTids:
            print(". "+each_tid+" is wounded as it is younger than "+requestingTid+", "+each_tid+" is aborted and releases item")
            abort(each_tid) #then update the lock according to requesting transaction
            displayFlag = 1
            execute(line,displayFlag)
    #if holding transactions consist of both older and younger transactions
    elif(len(youngerholdingTids)>0 and len(holdingOlderTransactions)>0):
        print("Because "+requestingTid+" is younger than "+str(holdingOlderTransactions)+","+requestingTid+ " waits on "+item+" to be release by "+str(holdingOlderTransactions)+"")
        transactionTable[requestingTid]['blockedBy'] = transactionTable[requestingTid]['blockedBy']+ holdingOlderTransactions
        waitingOps = blockTransaction(requestingTid,item,line)
        for each_tid in youngerholdingTids:
            print(". "+each_tid+" is wounded as it is younger than "+requestingTid+", "+each_tid+" is aborted and releases item ", end=' ')
            abort(each_tid)
    # if all the holdinding transactions are older than requesting transactions
    else:
        print("Because "+requestingTid+" is younger than "+str(holdingOlderTransactions)+","+requestingTid+ " waits on "+item+" to be release by "+str(holdingOlderTransactions)+"", end='')
        transactionTable[requestingTid]['blockedBy'] = transactionTable[requestingTid]['blockedBy']+ holdingOlderTransactions
        waitingOps = blockTransaction(requestingTid,item,line)
    
    #printing any waiting operations for blocked transactions
    if(len(waitingOps)>0):
        waitingOps = ','.join(waitingOps)
        print(" List of waiting operations of "+requestingTid+"->"+waitingOps)



#commiting transaction
def commit(currentTid,line):
    #set transaction status as commit in transaction table
    transactionTable[currentTid]['transactionStatus'] = "committed"
    
    print("Operation "+line+""+currentTid+" state = committed ")
    #print(transactionTable[currentTid]['ItemIds'])
    itemsString = (',').join(transactionTable[currentTid]['ItemIds'])
    print("Release locks held by "+currentTid+" i.e "+itemsString+" should be unlocked")
    for eachItem in transactionTable[currentTid]['ItemIds']:
        unlock(eachItem,currentTid)

#adding lock table content to dictionary
def addItemtoLockTable(item,state,currentTid):
    temp = {}
    temp['lockState'] = state
    temp['holdingTids'] = [currentTid];
    temp['waitingTids'] = [];
    lockTable[item] = temp

#begin transaction is added to transaction table
def beginTransaction(currentTid,line):
    #state set to active
    transactionTable[currentTid]['transactionStatus'] = "active"
    print("Operation "+line+"  Begin "+ currentTid+": Record is added to transaction table with Tid="+currentTid)
    print('')

    
# Read lock
def readLock(currentTid,line,item):
    if item not in lockTable:
        state = "read"
        #adding new item to lock table
        addItemtoLockTable(item,state,currentTid)
        #updating transaction table Items list
        transactionTable[currentTid]['ItemIds'].append(item)
        print("Operation "+line+" "+currentTid + " acquired read lock on item " +item)

    else:
        #for existing item, updating lock table and transaction table
        if lockTable[item]['lockState'] == "read" or lockTable[item]['lockState'] == "unlocked":
            lockTable[item]['holdingTids'].append(currentTid)
            transactionTable[currentTid]['ItemIds'].append(item)
            lockTable[item]['lockState'] = "read"
            print("Operation "+line+" "+currentTid+" has acquired read lock on "+ item)

        else:
            #conflit state, when item is write locked by other transactions
            woundWait(currentTid,item,line)



# Write Lock
def writeLock(currentTid,line,item):
    #if locked by current transaction read lock upgrade  to write lock
    holdingList = lockTable[item]['holdingTids']
    
    if lockTable[item]['lockState'] == "read" and currentTid in holdingList and len(holdingList)==1:
        #upgrade lock if item is read locked only by current transaction
        lockTable[item]['lockState'] = "write"
        print("Operation "+line+" Read lock upgraded to write lock for item " +item+ " by " + currentTid+", lock table updated to mode "+ lockTable[item]['lockState'])
    
    #acquire write lock if item is in unlocked state
    elif lockTable[item]['lockState'] == "unlocked":
        lockTable[item]['holdingTids'].append(currentTid)
        transactionTable[currentTid]['ItemIds'].append(item)
        print("current lock state upgraded to write lock for item " +item+ " by " + currentTid+", lock table updated to mode "+ lockTable[item]['lockState'])   
    else:
        #woundwait method called to deal with conflict state
        woundWait(currentTid,item,line)

#parsing to respective function based on input operation
def inputParser(currentTid,line,displayFlag):
    global timeStamp
    operation = line[0]
    item = '';
    print('\n')
    if operation=='r' or operation == 'w':
        item = line[3]
    if operation == 'b':
        timeStamp = timeStamp + 1
        temp = {}
        temp['ts'] = timeStamp
        temp['transactionStatus']=''
        temp['ItemIds']=[]
        temp['waitingOps'] = []
        temp['blockedBy']=[]
        transactionTable[currentTid] = temp
        beginTransaction(currentTid,line)
    if operation == 'r':
        readLock(currentTid,line,item)
    if operation == 'w':
        writeLock(currentTid,line,item)
    if operation == 'e':
        commit(currentTid,line)
    if(displayFlag == 0):
        displayTransactionTable = DisplayTransactiontable(transactionTable)
        lockTabledisplay = lockTableDisplay(lockTable)
        print(displayTransactionTable)
        print(lockTabledisplay)



#checking if input transaction is aborted or blocked and passing to inputparser
def execute(line,displayFlag=0):    
    currentTid = 'T'+ line[1]
    if currentTid not in transactionTable:
       if line[0] == 'b':
           inputParser(currentTid,line,displayFlag) 
    else:
         #if transaction is aborted it should be ignored
        if transactionTable[currentTid]['transactionStatus'] == "abort":  
                print(line+"Transaction already aborted. No changes in tables") 
        #for blocked transaction new operation is added to waiting list
        elif transactionTable[currentTid]['transactionStatus'] == "block":
            transactionTable[currentTid]['waitingOps'].append(line);
            waitingOps = ''.join(transactionTable[currentTid]['waitingOps'])
            print(line+" "+currentTid+" is blocked, we add this to list of waiting operation "+currentTid+"->"+waitingOps)
            displayTransactionTable = DisplayTransactiontable(transactionTable)
            lockTabledisplay = lockTableDisplay(lockTable)
            print(displayTransactionTable)
            print(lockTabledisplay)               
        else:
            inputParser(currentTid,line,displayFlag) 

    



#fileData_ consist of file and it is read line by line
for eachLine in fileData_:
    eachLine = eachLine.rstrip();
    #removing spaces in line
    eachLine = eachLine.replace(" ", "");
    if(eachLine != ''):
        execute(eachLine)  




                          
        


