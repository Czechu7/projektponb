namespace API.DTOs;
public class ChainResponse
{
    public List<Block> chain { get; set; }
    public int length { get; set; }
}