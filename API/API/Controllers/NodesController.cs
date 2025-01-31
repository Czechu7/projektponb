// API/Controllers/NodesController.cs
using API.DTOs;
using API.Services;
using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Json;
using System.Net.Sockets;
using System.Text;
using System.Xml.Linq;
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
        List<ChainResponse> responses = new List<ChainResponse>();
        foreach (var node in nodes)
        {
            try
            {
                if(node.Status == "inactive")
                {
                    continue;
                }

                var chainUrl = $"{node.Address}/chain";
                var chainResponse = await httpClient.GetFromJsonAsync<ChainResponse>(chainUrl);
                foreach (var item in chainResponse.chain)
                {
                    if(item.hash != "corrupted")
                    {
                                        responses.Add(chainResponse);

                    }
                }
                //if (chainResponse?.chain?.Count > 0)
                //{
                //    return Ok(chainResponse);
                //}
            }
            catch (Exception ex)
            {

            }
        }
        if(responses.Count > 0)
        {
            var maxLenght = responses.Max(x => x.length);

            return Ok(responses.FirstOrDefault(x => x.length == maxLenght));
        }
        else
        {
            return NotFound();

        }
    }

    [HttpPost("disableNode")]
    public async Task<IActionResult> DisableNode([FromBody] NodeStatus dto)
    {
        var nodes = _nodeStatusService.GetAllNodeStatuses();

        using var httpClient = new HttpClient();
        var chainUrl = $"{dto.Address}/simulated-shutdown";
        HttpContent content = new StringContent(" ", Encoding.UTF8, "application/json");

        try
        {
            var response = await httpClient.PostAsync(chainUrl, content);
            return Ok(new { message = "Request sent successfully" });
        }
        catch (HttpRequestException ex)
        {
            return StatusCode(200, new { message = "Node is shutting down, connection lost.", error = ex.Message });
        }
        catch (SocketException ex)
        {
            return StatusCode(200, new { message = "Connection was forcibly closed by the remote host.", error = ex.Message });
        }
    }


    [HttpPost("corruptHash")]
    public async Task<IActionResult> CorruptHash([FromBody] NodeStatus dto)
    {
        using var httpClient = new HttpClient();
        var chainUrl = $"{dto.Address}/simulated-crc-error";
        HttpContent content = new StringContent(" ", Encoding.UTF8, "application/json");
        try
        {
            var response = await httpClient.PostAsync(chainUrl, content);
            return Ok(new { message = "Request sent successfully" });
        }
        catch (HttpRequestException ex)
        {
            return StatusCode(200, new { message = "Node is shutting down, connection lost.", error = ex.Message });
        }
        catch (SocketException ex)
        {
            return StatusCode(200, new { message = "Connection was forcibly closed by the remote host.", error = ex.Message });
        }

 
    }

    [HttpPost("corruptFile")]
    public async Task<IActionResult> CorruptFile([FromBody] NodeStatus dto)
    {
        using var httpClient = new HttpClient();
        var chainUrl = $"{dto.Address}/simulated-hash";
        HttpContent content = new StringContent(" ", Encoding.UTF8, "application/json");
        try
        {
            var response = await httpClient.PostAsync(chainUrl, content);
            return Ok(new { message = "Request sent successfully" });
        }
        catch (HttpRequestException ex)
        {
            return StatusCode(200, new { message = "Node is shutting down, connection lost.", error = ex.Message });
        }
        catch (SocketException ex)
        {
            return StatusCode(200, new { message = "Connection was forcibly closed by the remote host.", error = ex.Message });
        }
        return Ok();
    }
    
    [HttpPost("corruptFileFix")]
    public async Task<IActionResult> CorruptFileFix([FromBody] NodeStatus dto)
    {
        using var httpClient = new HttpClient();
        var chainUrl = $"http://localhost:5001/simulated-hash-fix";
        HttpContent content = new StringContent(" ", Encoding.UTF8, "application/json");
        try
        {
            var response = await httpClient.PostAsync(chainUrl, content);
            return Ok(new { message = "Request sent successfully" });
        }
        catch (HttpRequestException ex)
        {
            return StatusCode(200, new { message = "Node is shutting down, connection lost.", error = ex.Message });
        }
        catch (SocketException ex)
        {
            return StatusCode(200, new { message = "Connection was forcibly closed by the remote host.", error = ex.Message });
        }
        return Ok();
    }


}