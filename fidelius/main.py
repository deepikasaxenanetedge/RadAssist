import os
import uuid
import json
import subprocess
import platform

from utils import getFideliusVersion

fideliusVersion = getFideliusVersion()
dirname = os.path.dirname(os.path.abspath(__file__))

# Correctly build path including the 'fidel' root folder
if platform.system() == 'Windows':
    binPath = os.path.abspath(os.path.join(
        dirname, f'fidelius-cli-{fideliusVersion}', 'bin', 'fidelius-cli.bat'
    ))
else:
    binPath = os.path.join(
        dirname, f'fidelius-cli-{fideliusVersion}', 'bin', 'fidelius-cli'
    )

print(f"Using Fidelius CLI executable: {binPath}")

cwd_dir = os.path.dirname(binPath)
if not os.path.isdir(cwd_dir):
    print(f"ERROR: cwd_dir '{cwd_dir}' is not a valid directory!")

def execFideliusCli(args):
    fideliusCommand = [binPath] + args
    shell_flag = True if platform.system() == 'Windows' else False

    if not os.path.isdir(cwd_dir):
        print(f"ERROR: cwd_dir '{cwd_dir}' is not a valid directory!")
        return None

    result = subprocess.run(
        fideliusCommand,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding='UTF-8',
        shell=shell_flag,
        cwd=cwd_dir
    )

    if result.returncode != 0:
        print(f"ERROR · execFideliusCli failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
        return None

    try:
        return json.loads(result.stdout)
    except Exception as e:
        print(f"ERROR · execFideliusCli JSON parse failed\nOutput:\n{result.stdout}\nException: {e}")
        return None


def getEcdhKeyMaterial():
    result = execFideliusCli(['gkm'])
    if result is None:
        print("Failed to get ECDH key material.")
    return result


def writeParamsToFile(*params):
    fileContents = '\n'.join(params)
    filePath = os.path.join(dirname, 'temp', f'{str(uuid.uuid4())}.txt')
    os.makedirs(os.path.dirname(filePath), exist_ok=True)
    with open(filePath, 'w') as f:
        f.write(fileContents)
    return filePath


def removeFileAtPath(filePath):
    os.remove(filePath)


def encryptData(encryptParams):
    paramsFilePath = writeParamsToFile(
        'e',
        encryptParams['stringToEncrypt'],
        encryptParams['senderNonce'],
        encryptParams['requesterNonce'],
        encryptParams['senderPrivateKey'],
        encryptParams['requesterPublicKey']
    )
    result = execFideliusCli(['-f', paramsFilePath])
    removeFileAtPath(paramsFilePath)
    return result


def decryptData(decryptParams):
    paramsFilePath = writeParamsToFile(
        'd',
        decryptParams['encryptedData'],
        decryptParams['requesterNonce'],
        decryptParams['senderNonce'],
        decryptParams['requesterPrivateKey'],
        decryptParams['senderPublicKey']
    )
    result = execFideliusCli(['-f', paramsFilePath])
    removeFileAtPath(paramsFilePath)
    return result


def runExample(stringToEncrypt):
    requesterKeyMaterial = getEcdhKeyMaterial()
    senderKeyMaterial = getEcdhKeyMaterial()

    if not requesterKeyMaterial or not senderKeyMaterial:
        print("Failed to get key materials. Exiting.")
        return

    print(json.dumps({
        'requesterKeyMaterial': requesterKeyMaterial,
        'senderKeyMaterial': senderKeyMaterial
    }, indent=4))

    encryptionResult = encryptData({
        'stringToEncrypt': stringToEncrypt,
        'senderNonce': senderKeyMaterial['nonce'],
        'requesterNonce': requesterKeyMaterial['nonce'],
        'senderPrivateKey': senderKeyMaterial['privateKey'],
        'requesterPublicKey': requesterKeyMaterial['publicKey']
    })

    encryptionWithX509PublicKeyResult = encryptData({
        'stringToEncrypt': stringToEncrypt,
        'senderNonce': senderKeyMaterial['nonce'],
        'requesterNonce': requesterKeyMaterial['nonce'],
        'senderPrivateKey': senderKeyMaterial['privateKey'],
        'requesterPublicKey': requesterKeyMaterial['x509PublicKey']
    })

    print(json.dumps({
        'encryptedData': encryptionResult['encryptedData'],
        'encryptedDataWithX509PublicKey': encryptionWithX509PublicKeyResult['encryptedData']
    }, indent=4))

    # **SWAPPED nonces here in decrypt calls**
    decryptionResult = decryptData({
        'encryptedData': encryptionResult['encryptedData'],
        'requesterNonce': senderKeyMaterial['nonce'],  # swapped
        'senderNonce': requesterKeyMaterial['nonce'],  # swapped
        'requesterPrivateKey': requesterKeyMaterial['privateKey'],
        'senderPublicKey': senderKeyMaterial['publicKey']
    })

    decryptionResultWithX509PublicKey = decryptData({
        'encryptedData': encryptionResult['encryptedData'],
        'requesterNonce': senderKeyMaterial['nonce'],  # swapped
        'senderNonce': requesterKeyMaterial['nonce'],  # swapped
        'requesterPrivateKey': requesterKeyMaterial['privateKey'],
        'senderPublicKey': senderKeyMaterial['x509PublicKey']
    })

    print(json.dumps({
        'decryptedData': decryptionResult['decryptedData'],
        'decryptedDataWithX509PublicKey': decryptionResultWithX509PublicKey['decryptedData']
    }, indent=4))


def main(stringToEncrypt='{"data": "There is no war in Ba Sing Se!"}'):
    runExample(stringToEncrypt)


if __name__ == '__main__':
    main()
