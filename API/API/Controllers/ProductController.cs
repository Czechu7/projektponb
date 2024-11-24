using API.Data;
using API.DTOs;
using API.Entities;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace API.Controllers
{
    public class ProductController(DataContext context) : BaseApiController
    {
        [AllowAnonymous]
        [HttpGet]
        public async Task<ActionResult<IEnumerable<Product>>> GetProducts()
        {
            var users = await context.Products.ToListAsync();

            return users;
        }
        [AllowAnonymous]
        [HttpGet("{id}")]
        public async Task<ActionResult<Product>> GetProductById(int id)
        {
            var product = await context.Products.FindAsync(id);

            if (product == null)
            {
                return NotFound();
            }

            return product;
        }

        [AllowAnonymous]
        [HttpPost]
        public async Task<ActionResult> Add(ProductDto product)
        {
            var productEntity = new Product
            {
                Name = product.Name,
                Quantity = product.Quantity,
                Price = product.Price
            };

            try
            {
                context.Products.Add(productEntity);
                await context.SaveChangesAsync();
                return Ok(product);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
                return StatusCode(500, new { Message = ex.Message });
            }

            return Ok();    
        }

    }
}
