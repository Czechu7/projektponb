// API/Models/NodeStatus.cs
namespace API.DTOs;
public class NodeStatus
{
    public string Address { get; set; }
    public string Status { get; set; }
    public DateTime LastUpdate { get; set; }
}