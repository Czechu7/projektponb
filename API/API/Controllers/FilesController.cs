using API.Data;
using API.Entities;
using API.Hubs;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.SignalR;
using Microsoft.EntityFrameworkCore;
using System.Security.Cryptography;

namespace API.Controllers
{
    public class FilesController(DataContext context, IHubContext<FileHub> _hubContext) : BaseApiController
    {
        private string UploadDirectory => Path.Combine(Directory.GetCurrentDirectory(), "uploads");

        [HttpPost]
        public async Task<IActionResult> UploadFile(IFormFile file)
        {
            if (file == null || file.Length == 0)
                return BadRequest("nie przesano pliku");

            if (!Directory.Exists(UploadDirectory))
                Directory.CreateDirectory(UploadDirectory);

            var filePath = Path.Combine(UploadDirectory, file.FileName);

            await using (var stream = new FileStream(filePath, FileMode.Create))
            {
                await file.CopyToAsync(stream);
            }

            string checksum;
            using (var sha256 = SHA256.Create())
            {
                await using var fileStream = new FileStream(filePath, FileMode.Open, FileAccess.Read);
                var hashBytes = await sha256.ComputeHashAsync(fileStream);
                checksum = BitConverter.ToString(hashBytes).Replace("-", "").ToLower();
                byte[] fileBytes = await System.IO.File.ReadAllBytesAsync(filePath);
                string fileBase64 = Convert.ToBase64String(fileBytes);
                await _hubContext.Clients.All.SendAsync("UploadFile", fileBase64, checksum);

            }

            var fileEntity = new FileEntity
            {
                FileName = file.FileName,
                FilePath = filePath,
                Checksum = checksum,
                SizeInBytes = file.Length,
                ContentType = file.ContentType,
                UploadedAt = DateTime.UtcNow,
                UploadedBy = User.Identity?.Name ?? " "
            };

            context.Files.Add(fileEntity);
            await context.SaveChangesAsync();

            return Ok(new { fileEntity.Id, fileEntity.FileName, fileEntity.Checksum });
        }

    }
}
