using Microsoft.AspNetCore.SignalR;

namespace API.Hubs
{
    public class FileHub : Hub
    {
        public async Task UploadFile(string fileName, string checksum)
        {
            await Clients.All.SendAsync("UploadFile", fileName, checksum);
        }
    }
}
