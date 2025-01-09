// API/Hubs/BlockchainHub.cs
using API.Services;
using Microsoft.AspNetCore.SignalR;
namespace API.Hubs;
public class BlockchainHub : Hub
{
    private readonly NodeStatusService _nodeStatusService;

    public BlockchainHub(NodeStatusService nodeStatusService)
    {
        _nodeStatusService = nodeStatusService;
    }

    public async Task UpdateNodeStatus(string nodeAddress, string status)
    {
        _nodeStatusService.UpdateNodeStatus(nodeAddress, status);
        await Clients.All.SendAsync("ReceiveNodeStatus", nodeAddress, status);
    }

    public async Task BroadcastNewBlock(string nodeAddress, string blockData)
    {
        await Clients.All.SendAsync("ReceiveNewBlock", nodeAddress, blockData);
    }
}