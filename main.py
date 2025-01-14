import zstandard
import random
import string
import os
import struct
import sys

tempDir = "./Tmp/"

Verbose = True

maps = {
    "837214085": "Clubhouse",
    "305979357167" : "Border",
    "1460220617" : "Kanal",
    "276279025182" : "Skyscraper",
    "53627213396" : "Tower",
    "259816839773" : "Chalet",
    "355496559878" : "Bank",
    "231702797556" : "Oregon",
    "1378191338" : "Kafe Dostoyevsky"
}

def verbose(data,end=None):
    if(Verbose):
        print(data,end=end)

def random_sting(n):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def getHeader(path):
    with open(path, 'rb') as fh:
        magic_check = fh.read(4)
        if magic_check != b'\x28\xb5\x2f\xfd':
            return None
        
        tempFile = tempDir + random_sting(16) + ".compressed"
        leadingFile = open(tempFile,"wb")
        leadingFile.write(magic_check)

        #wait till next file
        while data := fh.read(1):
            if data == b'\x28':
                rest_magic = fh.read(3)
                if rest_magic == b'\xb5\x2f\xfd':
                    #file completed
                    leadingFile.close()
                    return tempFile
                else:
                    leadingFile.write(data)
                    leadingFile.write(rest_magic)
            else:
                leadingFile.write(data)

def extract(filename,delete = False):  
    try:
        output = tempDir + random_sting(16) + ".decompressed"
        stream = open(filename, "rb")
        f = open(output , "wb")
        dctx = zstandard.ZstdDecompressor()
        reader = dctx.stream_reader(stream)
        while True:
            chunk = reader.read(16384)
            if not chunk:
                break
            f.write(chunk)
        f.close()
        stream.close()
        return output
    except zstandard.ZstdError:
        print("location?= " + str(stream.tell()))
        print("filename = " + output)
        # TODO: it kindof crashes here on the last stream. fails to find the zstd frame
        f.close()
        stream.close()
        return None
    finally:
        if(delete):
            os.remove(filename)

def convert(data):
    return " ".join("{:02x}".format(x) for x in data)

def get_string(fh):
    #value = struct.unpack('B', fh.read(1)[0])[0]
    value = struct.unpack('B', fh.read(1))[0]
    if(fh.read(7) != b'\x00\x00\x00\x00\x00\x00\x00'):
        print("String Check Failed")
        return None
    return fh.read(value).decode('UTF-8')

def get_settings(fh):
    variable = get_string(fh)
    if variable == None:
        print("Failed Getting Setting")
    value = get_string(fh)
    return (variable,value)

def worldid(settings):
    print("MAP : " + maps.get(settings[1],settings[1]),)

def round_number(settings,fh):
    overtimeround = int(get_settings(fh)[1]) +  int(settings[1])
    print("Round Number : " + str(overtimeround))

def get_player(last,fh):
    playerid = last[1]
    playerName = get_settings(fh)[1]
    team = get_settings(fh)[1]
    heroname = get_settings(fh)[1]
    alliance = get_settings(fh)[1]
    roleimage =  get_settings(fh)[1]
    rolename = get_settings(fh)[1]
    roleportrait =  get_settings(fh)[1]
    print(playerName + " : " + rolename )
    
#MAYBE NO CLUE IF THIS IS THE LOADOUT 
def get_loadout_packet(fh,special_bytes):
    code = fh.read(2)
    code2 = fh.read(3)
    data = fh.read(7)
    verbose(convert(code + code2) + " : " + convert(data))
    if(special_bytes == code):
        verbose("7 00 bytes "+convert(fh.read(7)))
        code = fh.read(29)
        verbose(convert(code[0:2]) + " : "+convert(code[2:]))
        return False
    return True

def get_spec_packet(fh,special_byte):
    code = fh.read(2)
    if convert(code) == "62 73" or convert(code) == "61 73":
        fh.seek(-2,1)
        return False
    else:
        data = fh.read(27)
        verbose(convert(code[0:2]) + " : "+convert(data))
        return code+data

def get_unknown_bytes(fh):

    # code = fh.read(2)
    # data = fh.read(114)
    # verbose(convert(code + data))
    # return code + data
    last_zero = False
    while byte := fh.read(1):
        if convert(byte) == "00" and last_zero == False:
            last_zero = True
            verbose('')
        elif convert(byte) != "00" and last_zero == True:
            last_zero = False
            verbose('')
        verbose(convert(byte),end=" ")

def getInfo(filename,delete = False):
    with open(filename, 'rb') as fh:
        if fh.read(7) != b'dissect':
            print("not dissect")
        
        verbose("number after dissect : " + convert(fh.read(2)))   
        verbose("3 bytes 00  no clue : " + convert(fh.read(3)))
        verbose("Dissect Version? : " + get_string(fh))
        verbose("4 bytes of 00 no clue : " + convert(fh.read(4)))
        special_bytes = fh.read(2)
        verbose("special? bytes :" + convert(special_bytes))
        verbose("10 bytes no clue : " + convert(fh.read(10)))

        while settings := get_settings(fh) :
            if(settings[0] == "id"):
                print("MatchID : " + settings[1])
                break
            elif(settings[0] == "playerid"):
                get_player(settings,fh)
            elif(settings[0] == "roundnumber"):
                round_number(settings,fh)
            elif settings[0] == "worldid":
                worldid(settings)
            else:
                verbose("Data : "+ settings[0] + " ------  " + settings[1])
        
        verbose("24 bytes no clue : " + convert(fh.read(24)))

        while get_loadout_packet(fh,special_bytes):
            continue

        while get_spec_packet(fh,special_bytes):
            continue

        while get_unknown_bytes(fh):
            continue

        while data := fh.read(8):
            verbose(convert(data))

    if(delete):
        os.remove(filename)

def main():
    #ensure_dir(location)

    ensure_dir(tempDir)
    if len(sys.argv) < 2:
        print("usage: python main.py <file_path>")
        return
    filename = sys.argv[1]
    if not os.path.isfile(filename):
        print("File does not exist")
        return

    temp = getHeader(filename)
    if(temp == None):
        print("Check file : Could not find magic")
    extracted = extract(temp,True)
    if(extracted == None):
        print("Check file : Extraction Failed")
    getInfo(extracted,True)

if __name__ == "__main__":
    main()