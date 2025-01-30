namespace API.DTOs;
public class Block
{
    public int index { get; set; }
    public string previous_hash { get; set; }
    public object transactions { get; set; }  
    public double timestamp { get; set; }
    public string hash { get; set; }
}