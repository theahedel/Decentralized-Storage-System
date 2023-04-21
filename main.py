import os,hashlib,pickle
from cryptography.fernet import Fernet

class Network:
    def __init__(self, ID=None):
        self.ID = ID
        self.NodeList = []
        self.DHT = {}
    
    def InitializeNodes(self):
        nodes_path = os.path.join(get_executed_folder_path(), 'Nodes')
        i = 1
        for x in list_contents(nodes_path):
            newNode = Node(1, os.path.join(nodes_path, str(i)), self)
            self.NodeList.append(newNode)
            
            i+=1
    
    def requestFileObj(self, fileHash):
        for x in self.NodeList:
            cache_folder = os.path.join(x.NodePath, "Cache")
            cache_contents = list_contents(cache_folder)
            
            for x in cache_contents:
                full_path = os.path.join(cache_folder, x)
                
                with open(full_path, 'rb') as f:
                    obj = pickle.load(f)
                    
                    if obj.id == fileHash:
                        return obj
                    
        return None
            
    
class Node:
    def __init__(self, ID, NodePath, network):
        self.id = ID        
        self.NodePath = NodePath
        self.Network = network
        self.fileTable = []
    
    
    def uploadFile(self, file_path):
        try:
            head_tail = os.path.split(file_path)
            key = generate_key()
            with open(file_path, 'rb') as file:
                
                chunks = []
                
                while True:
                    chunk = file.read(256*1024)
                    
                    if not chunk:
                        break
                    
                
                    ChunkID = hashlib.sha256(chunk).hexdigest()
                    encrypted_chunk = encrypt_chunk(chunk, key)
                    chunks.append(ChunkID)
                    newObj=Object(ChunkID,encrypted_chunk,None)
                    
                    with open(os.path.join(self.NodePath,"Cache",f"{ChunkID}.enc"), "wb+") as f:
                        pickle.dump(newObj, f)
                
                
                
                LinkObjID = hashlib.sha256((str(chunks)).encode('utf-8')).hexdigest()
                LinkObj = Object(LinkObjID, [head_tail[1],key], chunks)
                
                with open(os.path.join(self.NodePath,"Cache",f"{LinkObjID}.enc"), "wb+") as f:
                    pickle.dump(LinkObj, f)
                
                self.fileTable.append(LinkObj)
                self.Network.DHT[f"{LinkObjID}"] = LinkObj
                
                
                print(f"[NODE: {self.id}] - Uploaded the file {head_tail[1]} in cache. File is now avaialble in network as hash: {LinkObjID}")
                return LinkObjID

        except FileNotFoundError:
            print(f"The file '{file_path}' was not found.")
        except PermissionError:
            print(f"Permission denied to access the file '{file_path}'.")
        except Exception as e:
            print(f"An error occurred: {e}")
    
    def requestFile(self, LinkObjHash):
        try:
            fileToGet = None
            for f in self.fileTable:
                if f.id == LinkObjHash:
                    fileToGet = f
            else:
                if fileToGet == None:
                    for f in self.Network.DHT.keys():
                        if LinkObjHash == f:
                            fileToGet = self.Network.DHT[f]
            
            if fileToGet == None:
                fileToGet = self.Network.requestFileObj(LinkObjHash)
            
            
            outputFileName = f"{fileToGet.Data[0]}"
            
            pathToFile = f"{self.NodePath}/Downloaded/{outputFileName}"
            
            
            with open(pathToFile, 'wb+') as decryptedFile:
                for i in fileToGet.Link:
                    encryptedObj = self.Network.requestFileObj(i)
                    decryptedChunk = decrypt_chunk(encryptedObj.Data, fileToGet.Data[1])
                    decryptedFile.write(decryptedChunk)
            
            print(f"[NODE: {self.id}] - Downloaded the file {outputFileName} in Downloaded folder. File is now avaialble in the node.")
        except FileNotFoundError:
            print(f"One of the encrypted chunk files was not found.")
        except PermissionError:
            print(f"Permission denied to access one of the encrypted chunk files.")
        except Exception as e:
            print(f"An error occurred: {e}")
        
class Object:
    def __init__(self, ID, Data, Link):
        self.id = ID
        self.Link = Link
        self.Data = Data
        

def generate_key():
    return Fernet.generate_key()

def encrypt_chunk(chunk, key):
    fernet = Fernet(key)
    return fernet.encrypt(chunk)

def decrypt_chunk(chunk, key):
    fernet = Fernet(key)
    return fernet.decrypt(chunk)

def list_contents(folder_path):
    try:
        contents = os.listdir(folder_path)
        output = []
        for item in contents:
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                if item not in output:
                    output.append(str(item_path))
            elif os.path.isdir(item_path):
                output.append(list_contents(item_path))
            else:
                print(f"Unknown: {item}")
        
        return output
    except FileNotFoundError:
        print(f"The folder '{folder_path}' was not found.")
    except PermissionError:
        print(f"Permission denied to access the folder '{folder_path}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

def get_executed_folder_path():
    script_folder = os.path.dirname(os.path.abspath(__file__))
    return script_folder


newNetwork = Network()
newNetwork.InitializeNodes()
while True:
    
    
    for i in newNetwork.NodeList:
        PathOfNode = i.NodePath
        
        UploadContent = list_contents(os.path.join(PathOfNode, 'Upload'))
        CommandPromptPath = os.path.join(PathOfNode, 'CommandPrompt.txt')
        with open(CommandPromptPath, 'r') as commandPromptFile:
            
            content = commandPromptFile.read()
            
            
            if content != "":
                if (content.split())[0] == "DOWNLOAD":
                    i.requestFile((content.split())[1])
                elif (content.split())[0] == "UPLOAD":
                    for x in UploadContent:
                        i.uploadFile(x)
    break
   