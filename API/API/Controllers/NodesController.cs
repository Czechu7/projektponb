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
    public IEnumerable<NodeStatus> GetNodeStatuses()
    {
        return _nodeStatusService.GetAllNodeStatuses();
    }

    [HttpPost("disableNode")]
    public async Task<IActionResult> DisableNode([FromBody] NodeStatus dto)
    {
        return Ok();
    }

    [HttpPost("corruptHash")]
    public async Task<IActionResult> CorruptHash([FromBody] NodeStatus dto)
    {
        return Ok();
    }

    [HttpPost("corruptFile")]
    public async Task<IActionResult> CorruptFile([FromBody] NodeStatus dto)
    {
        return Ok();
    }


}