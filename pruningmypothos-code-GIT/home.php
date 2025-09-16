<?php get_header(); ?>

<div class="container blog-container">
  <h1>Blog</h1>

  <?php if (have_posts()) : ?>
    <div class="blog-grid">
      <?php while (have_posts()) : the_post(); ?>
        <article class="post-card">
          <?php if (has_post_thumbnail()) : ?>
            <a href="<?php the_permalink(); ?>">
              <?php the_post_thumbnail('medium', ['loading' => 'lazy']); ?>
            </a>
          <?php endif; ?>

          <h2 class="post-title">
            <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
          </h2>

          <p><?php echo wp_trim_words(get_the_excerpt(), 20); ?></p>
        </article>
      <?php endwhile; ?>
    </div>

    <!-- Pagination -->
    <div class="pagination">
      <?php the_posts_pagination([
        'prev_text' => '&laquo; Previous',
        'next_text' => 'Next &raquo;',
        'screen_reader_text' => 'Posts navigation'
      ]); ?>
    </div>

  <?php else : ?>
    <p>No posts found.</p>
  <?php endif; ?>
</div>

<?php get_footer(); ?>
