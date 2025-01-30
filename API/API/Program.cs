using System.Text;
using System.Text.Json.Serialization;
using System.Text.Json;
using API.Data;
using API.Extensions;
using API.Interfaces;
using API.Middleware;
using API.Services;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using API.Hubs;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddSignalR();
// Program.cs
builder.Services.AddSingleton<NodeStatusService>();
builder.Services.AddApplicationService(builder.Configuration);
builder.Services.AddIdentityServices(builder.Configuration);
builder.Services.AddSignalR();

builder.Services.Configure<Microsoft.AspNetCore.Http.Json.JsonOptions>(options =>
{
    options.SerializerOptions.ReferenceHandler = ReferenceHandler.IgnoreCycles;
});

builder.Services.AddCors(options =>
{
    options.AddPolicy("CorsPolicy", builder => 
        builder
            .SetIsOriginAllowed(_ => true) // Allow any origin
            .AllowAnyHeader()
            .AllowAnyMethod()
            .AllowCredentials());
});

var app = builder.Build();
if (app.Environment.IsDevelopment())
{
    // U�yj Swagger w �rodowisku developerskim
    app.UseSwagger();
    app.UseSwaggerUI(c =>
    {
        c.SwaggerEndpoint("/swagger/v1/swagger.json", "My API V1");
        c.RoutePrefix = string.Empty; // Ustaw na pusty, aby wywo�a� / zamiast /swagger
    });
}
app.UseMiddleware<ExceptionMiddleware>();

app.UseCors("CorsPolicy");
// app.UseCors(x => x.AllowAnyHeader().AllowAnyMethod()
//     .WithOrigins(
//         "http://localhost:4200",
//         "https://localhost:4200",
//         "http://localhost:5001",
//         "https://localhost:5002",
//         "http://localhost:5003",
//         "https://localhost:5004",
//         "http://localhost:5005",
//         "https://localhost:5006",
//         "http://localhost:4999" 
//     ));
// Example configuration for your JsonSerializerOptions
// API/Program.cs


// In app configuration
app.MapHub<BlockchainHub>("/blockchainhub");
app.UseAuthentication();
app.UseAuthorization();

// Configure the HTTP request pipeline.
app.MapControllers();
app.MapHub<FileHub>("/hub");

app.Run();
