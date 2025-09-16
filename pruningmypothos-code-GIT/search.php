<?php
/**
 * Template for Search Results
 */
get_header(); ?>

<div class="container">
  <h2>Search Results for: <?php echo get_search_query(); ?></h2>

  <?php if (have_posts()) : ?>
    <div class="blog-grid">
      <?php while (have_posts()) : the_post(); ?>
        <article class="post-card">
          <?php if (has_post_thumbnail()) : ?>
            <a href="<?php the_permalink(); ?>">
              <?php the_post_thumbnail('medium', ['loading' => 'lazy']); ?>
            </a>
          <?php endif; ?>
          <h3 class="post-title"><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h3>
          <p><?php echo wp_trim_words(get_the_excerpt(), 20); ?></p>
        </article>
      <?php endwhile; ?>
    </div>

    <!-- Pagination -->
    <div class="pagination">
      <?php
      echo paginate_links([
        'total' => $wp_query->max_num_pages
      ]);
      ?>
    </div>

  <?php else : ?>
    <p>No results found for "<?php echo get_search_query(); ?>"</p>
  <?php endif; ?>
</div>

<?php get_footer(); ?>
