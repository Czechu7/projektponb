// API/Services/NodeStatusService.cs
using API.DTOs;

namespace API.Services;
public class NodeStatusService
{
    private readonly Dictionary<string, NodeStatus> _nodeStatuses = new();
    private readonly ILogger<NodeStatusService> _logger;

    public NodeStatusService(ILogger<NodeStatusService> logger)
    {
        _logger = logger;
    }


    public void UpdateNodeStatus(string nodeAddress, string status)
    {
        _nodeStatuses[nodeAddress] = new NodeStatus
        {
            Address = nodeAddress,
            Status = status,
            LastUpdate = DateTime.UtcNow
        };
        _logger.LogInformation($"Node {nodeAddress} status updated to {status}");
    }

    public IEnumerable<NodeStatus> GetAllNodeStatuses()
    {
        // Mark nodes as inactive if not updated in last 30 seconds
        var threshold = DateTime.UtcNow.AddSeconds(-30);
        foreach (var status in _nodeStatuses.Values)
        {
            if (status.LastUpdate < threshold && status.Status != "inactive")
            {
                UpdateNodeStatus(status.Address, "inactive");
            }
        }
        return _nodeStatuses.Values;
    }
}