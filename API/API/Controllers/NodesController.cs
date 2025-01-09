// API/Controllers/NodesController.cs
using API.DTOs;
using API.Services;
using Microsoft.AspNetCore.Mvc;

namespace API.Controllers;
// API/Controllers/NodesController.cs
[ApiController]
[Route("api/[controller]")]
public class NodesController(NodeStatusService nodeStatusService) : ControllerBase
{
    private readonly NodeStatusService _nodeStatusService = nodeStatusService;

    [HttpGet]
    public ActionResult<IEnumerable<NodeStatus>> GetNodeStatuses()
    {
        // Initialize default statuses if empty
        if (!_nodeStatusService.GetAllNodeStatuses().Any())
        {
            for (int port = 5001; port <= 5006; port++)
            {
                _nodeStatusService.UpdateNodeStatus($"http://localhost:{port}", "unknown");
            }
        }
        
        return Ok(_nodeStatusService.GetAllNodeStatuses());
    }
}