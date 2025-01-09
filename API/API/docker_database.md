#### Docker start

```
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=P@ssw0rd" -e "MSSQL_PID=Express" -p 1433:1433 -d --name=sql mcr.microsoft.com/mssql/server:latest
```

#### Conntection strings

```
"ConnectionStrings": {
	"DefaultConnection": "Server=localhost,1433;Initial Catalog=bai;User Id=sa;Password=P@ssw0rd;TrustServerCertificate=True"
}
```

#### Database update

```
dotnet ef database update
```
