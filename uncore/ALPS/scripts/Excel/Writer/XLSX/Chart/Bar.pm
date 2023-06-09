package Excel::Writer::XLSX::Chart::Bar;

###############################################################################
#
# Bar - A class for writing Excel Bar charts.
#
# Used in conjunction with Excel::Writer::XLSX::Chart.
#
# See formatting note in Excel::Writer::XLSX::Chart.
#
# Copyright 2000-2011, John McNamara, jmcnamara@cpan.org
#
# Documentation after __END__
#

# perltidy with the following options: -mbl=2 -pt=0 -nola

use 5.008002;
use strict;
use warnings;
use Carp;
use Excel::Writer::XLSX::Chart;

our @ISA     = qw(Excel::Writer::XLSX::Chart);
our $VERSION = '0.39';


###############################################################################
#
# new()
#
#
sub new {

    my $class = shift;
    my $self  = Excel::Writer::XLSX::Chart->new( @_ );

    $self->{_subtype}           = $self->{_subtype} || 'clustered';
    $self->{_cat_axis_position} = 'l';
    $self->{_val_axis_position} = 'b';
    $self->{_horiz_val_axis}    = 0;
    $self->{_horiz_cat_axis}    = 1;

    bless $self, $class;

    return $self;
}


##############################################################################
#
# _write_chart_type()
#
# Override the virtual superclass method with a chart specific method.
#
sub _write_chart_type {

    my $self = shift;

    # Reverse X and Y axes for Bar charts.
    my $tmp = $self->{_y_axis};
    $self->{_y_axis} = $self->{_x_axis};
    $self->{_x_axis} = $tmp;

    # Write the c:barChart element.
    $self->_write_bar_chart();
}


##############################################################################
#
# _write_bar_chart()
#
# Write the <c:barChart> element.
#
sub _write_bar_chart {

    my $self = shift;
    my $subtype = $self->{_subtype};

    $subtype = 'percentStacked' if $subtype eq 'percent_stacked';

    $self->{_writer}->startTag( 'c:barChart' );

    # Write the c:barDir element.
    $self->_write_bar_dir();

    # Write the c:grouping element.
    $self->_write_grouping( $subtype );

    # Write the series elements.
    $self->_write_series();

    $self->{_writer}->endTag( 'c:barChart' );
}


##############################################################################
#
# _write_bar_dir()
#
# Write the <c:barDir> element.
#
sub _write_bar_dir {

    my $self = shift;
    my $val  = 'bar';

    my @attributes = ( 'val' => $val );

    $self->{_writer}->emptyTag( 'c:barDir', @attributes );
}


##############################################################################
#
# _write_series()
#
# Over-ridden to add c:overlap.
#
# Write the series elements.
#
sub _write_series {

    my $self = shift;

    # Write each series with subelements.
    my $index = 0;
    for my $series ( @{ $self->{_series} } ) {
        $self->_write_ser( $index++, $series );
    }

    # Write the c:marker element.
    $self->_write_marker_value();

    # Write the c:overlap element.
    $self->_write_overlap() if $self->{_subtype} =~ /stacked/;

    # Generate the axis ids.
    $self->_add_axis_id();
    $self->_add_axis_id();

    # Write the c:axId element.
    $self->_write_axis_id( $self->{_axis_ids}->[0] );
    $self->_write_axis_id( $self->{_axis_ids}->[1] );
}


##############################################################################
#
# _write_num_fmt()
#
# Over-ridden to add % format. TODO. This will be refactored back up to the
# SUPER class later.
#
# Write the <c:numFmt> element.
#
sub _write_number_format {

    my $self          = shift;
    my $format_code   = shift || 'General';
    my $source_linked = 1;

    if ($self->{_subtype} eq 'percent_stacked') {
        $format_code = '0%';
    }

    my @attributes = (
        'formatCode'   => $format_code,
        'sourceLinked' => $source_linked,
    );

    $self->{_writer}->emptyTag( 'c:numFmt', @attributes );
}


1;


__END__


=head1 NAME

Bar - A class for writing Excel Bar charts.

=head1 SYNOPSIS

To create a simple Excel file with a Bar chart using Excel::Writer::XLSX:

    #!/usr/bin/perl

    use strict;
    use warnings;
    use Excel::Writer::XLSX;

    my $workbook  = Excel::Writer::XLSX->new( 'chart.xlsx' );
    my $worksheet = $workbook->add_worksheet();

    my $chart     = $workbook->add_chart( type => 'bar' );

    # Configure the chart.
    $chart->add_series(
        categories => '=Sheet1!$A$2:$A$7',
        values     => '=Sheet1!$B$2:$B$7',
    );

    # Add the worksheet data the chart refers to.
    my $data = [
        [ 'Category', 2, 3, 4, 5, 6, 7 ],
        [ 'Value',    1, 4, 5, 2, 1, 5 ],
    ];

    $worksheet->write( 'A1', $data );

    __END__

=head1 DESCRIPTION

This module implements Bar charts for L<Excel::Writer::XLSX>. The chart object is created via the Workbook C<add_chart()> method:

    my $chart = $workbook->add_chart( type => 'bar' );

Once the object is created it can be configured via the following methods that are common to all chart classes:

    $chart->add_series();
    $chart->set_x_axis();
    $chart->set_y_axis();
    $chart->set_title();

These methods are explained in detail in L<Excel::Writer::XLSX::Chart>. Class specific methods or settings, if any, are explained below.

=head1 Bar Chart Methods

The C<Bar> chart module also supports the following sub-types:

    stacked
    percent_stacked

These can be specified at creation time via the C<add_chart()> Worksheet method:

    my $chart = $workbook->add_chart( type => 'bar', subtype => 'stacked' );

=head1 EXAMPLE

Here is a complete example that demonstrates most of the available features when creating a chart.

    #!/usr/bin/perl

    use strict;
    use warnings;
    use Excel::Writer::XLSX;

    my $workbook  = Excel::Writer::XLSX->new( 'chart_bar.xlsx' );
    my $worksheet = $workbook->add_worksheet();
    my $bold      = $workbook->add_format( bold => 1 );

    # Add the worksheet data that the charts will refer to.
    my $headings = [ 'Number', 'Batch 1', 'Batch 2' ];
    my $data = [
        [ 2,  3,  4,  5,  6,  7 ],
        [ 10, 40, 50, 20, 10, 50 ],
        [ 30, 60, 70, 50, 40, 30 ],

    ];

    $worksheet->write( 'A1', $headings, $bold );
    $worksheet->write( 'A2', $data );

    # Create a new chart object. In this case an embedded chart.
    my $chart = $workbook->add_chart( type => 'bar', embedded => 1 );

    # Configure the first series.
    $chart->add_series(
        name       => '=Sheet1!$B$1',
        categories => '=Sheet1!$A$2:$A$7',
        values     => '=Sheet1!$B$2:$B$7',
    );

    # Configure second series. Note alternative use of array ref to define
    # ranges: [ $sheetname, $row_start, $row_end, $col_start, $col_end ].
    $chart->add_series(
        name       => '=Sheet1!$C$1',
        categories => [ 'Sheet1', 1, 6, 0, 0 ],
        values     => [ 'Sheet1', 1, 6, 2, 2 ],
    );

    # Add a chart title and some axis labels.
    $chart->set_title ( name => 'Results of sample analysis' );
    $chart->set_x_axis( name => 'Test number' );
    $chart->set_y_axis( name => 'Sample length (mm)' );

    # Set an Excel chart style. Blue colors with white outline and shadow.
    $chart->set_style( 11 );

    # Insert the chart into the worksheet (with an offset).
    $worksheet->insert_chart( 'D2', $chart, 25, 10 );

    __END__


=begin html

<p>This will produce a chart that looks like this:</p>

<p><center><img src="http://homepage.eircom.net/~jmcnamara/perl/images/2007/bar1.jpg" width="483" height="291" alt="Chart example." /></center></p>

=end html


=head1 AUTHOR

John McNamara jmcnamara@cpan.org

=head1 COPYRIGHT

Copyright MM-MMXI, John McNamara.

All Rights Reserved. This module is free software. It may be used, redistributed and/or modified under the same terms as Perl itself.

