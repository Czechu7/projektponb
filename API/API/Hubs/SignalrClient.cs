//using Microsoft.AspNetCore.SignalR.Client;

//namespace API.Hubs
//{
//    public class SignalRClient
//    {
//        private readonly string _hubUrl = "http://localhost:8081/hub";  
//        private HubConnection _connection;

//        public async Task InitializeConnection()
//        {
//            _connection = new HubConnectionBuilder()
//                .WithUrl(_hubUrl)
//                .Build();

                //tu jest receive
//            _connection.On<string, string, string>("UploadFile", (fileInfo, fileBytes, checksum) =>
//            {
//                Console.WriteLine($"Received file info: {fileInfo}");
//            });

//            _connection.Closed += async (exception) =>
//            {
//                Console.WriteLine("Connection closed. Attempting to reconnect...");
//                await Task.Delay(5000);  
//                await InitializeConnection();  
//            };

//            await _connection.StartAsync();
//            Console.WriteLine("Connection established.");
//        }

//        public async Task SendFileToPythonHub(string fileName, string fileBytes, string fileHash)
//        {
//            if (_connection == null)
//            {
//                Console.WriteLine("Connection not initialized.");
//                return;
//            }

//            while (_connection.State != HubConnectionState.Connected)
//            {
//                Console.WriteLine("Waiting for connection to be established...");
//                await Task.Delay(1000);  
//            }

//            try
//            {

//                await _connection.InvokeAsync("UploadFile", fileName, fileHash);

//                Console.WriteLine($" {fileName} sent to Python server.");
//            }
//            catch (ArgumentNullException argEx)
//            {
//                Console.WriteLine($"ArgumentNullException: {argEx.Message}");
//            }
//            catch (Exception ex)
//            {
//                Console.WriteLine($"Error sending file: {ex.Message}");
//            }
//        }


//    }
//}
