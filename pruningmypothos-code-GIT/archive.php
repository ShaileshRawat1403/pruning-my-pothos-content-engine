<?php
get_header();
?>

<section class="archive-hero-section fade-in">
  <div class="container">
    <h1 class="archive-title"><?php echo get_the_archive_title(); ?></h1>
    <?php if (term_description()) : ?>
      <p class="archive-description"><?php echo term_description(); ?></p>
    <?php else : ?>
      <p class="archive-description">A collection of thoughts, notes, and stories rooted in this theme.</p>
    <?php endif; ?>
  </div>
</section>

<section class="blog-container">
  <div class="container">
    <?php if (have_posts()) : ?>
      <div class="blog-grid">
        <?php while (have_posts()) : the_post(); ?>
          <article class="post-card">
            <?php if (has_post_thumbnail()) : ?>
              <a href="<?php the_permalink(); ?>">
                <?php the_post_thumbnail('medium', ['loading' => 'lazy']); ?>
              </a>
            <?php endif; ?>
            <h2 class="post-title"><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
            <p><?php echo wp_trim_words(get_the_excerpt(), 20); ?></p>
          </article>
        <?php endwhile; ?>
      </div>

      <div class="pagination">
        <?php the_posts_pagination([
          'prev_text' => '← Newer',
          'next_text' => 'Older →',
        ]); ?>
      </div>
    <?php else : ?>
      <p class="no-posts">No posts found in this archive. Maybe they're still sprouting.</p>
    <?php endif; ?>
  </div>
</section>

<?php
get_footer();
?>
