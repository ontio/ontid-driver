# ONT ID Driver

Driver for ONT ID to be used in [Universal Resolver](https://github.com/decentralized-identity/universal-resolver)


## Usage

Build docker image

```
docker build -f ./Dockerfile . -t ontio/ontid-driver
```

Start a container

```
docker run -p 8080:8080 ontio/ontid-driver
```

Test resolving ONT ID

```
curl -X GET http://localhost:8080/1.0/identifiers/did:ont:AN5g6gz9EoQ3sCNu7514GEghZurrktCMiH
```
