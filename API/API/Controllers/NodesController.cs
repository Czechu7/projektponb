// API/Controllers/NodesController.cs
using API.DTOs;
using API.Services;
using Microsoft.AspNetCore.Mvc;
using System.Net.Http.Json;
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


    [HttpGet("merged-chain")]
    public async Task<ActionResult<ChainResponse>> GetMergedChain()
    {
        var nodes = _nodeStatusService.GetAllNodeStatuses();
        using var httpClient = new HttpClient();

        foreach (var node in nodes)
        {
            try
            {
                var chainUrl = $"{node.Address}/chain";
                var chainResponse = await httpClient.GetFromJsonAsync<ChainResponse>(chainUrl);
                if (chainResponse?.chain?.Count > 0)
                {
                    return Ok(chainResponse);
                }
            }
            catch (Exception ex)
            {

            }
        }

        return NotFound();
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