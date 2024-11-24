namespace API.Entities
{
    public class Cart
    {
        public int Id { get; set; }
        public int UserId { get; set; }
        public int ProductId { get; set; }
        public virtual Product Product { get; set; }
        public virtual AppUser User { get; set; }
    }
}
