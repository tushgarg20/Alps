package Excel::Writer::XLSX::Package::Relationships;

###############################################################################
#
# Relationships - A class for writing the Excel XLSX Rels file.
#
# Used in conjunction with Excel::Writer::XLSX
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
use Excel::Writer::XLSX::Package::XMLwriter;

our @ISA     = qw(Excel::Writer::XLSX::Package::XMLwriter);
our $VERSION = '0.39';

our $schema_root     = 'http://schemas.openxmlformats.org';
our $package_schema  = $schema_root . '/package/2006/relationships';
our $document_schema = $schema_root . '/officeDocument/2006/relationships';

###############################################################################
#
# Public and private API methods.
#
###############################################################################


###############################################################################
#
# new()
#
# Constructor.
#
sub new {

    my $class = shift;
    my $self  = Excel::Writer::XLSX::Package::XMLwriter->new();

    $self->{_writer} = undef;
    $self->{_rels}   = [];
    $self->{_id}     = 1;

    bless $self, $class;

    return $self;
}


###############################################################################
#
# _assemble_xml_file()
#
# Assemble and write the XML file.
#
sub _assemble_xml_file {

    my $self = shift;

    return unless $self->{_writer};

    $self->_write_xml_declaration;
    $self->_write_relationships();
}


###############################################################################
#
# _add_document_relationship()
#
# Add container relationship to XLSX .rels xml files.
#
sub _add_document_relationship {

    my $self   = shift;
    my $type   = shift;
    my $target = shift;

    $type   = $document_schema . $type;
    $target = $target;

    push @{ $self->{_rels} }, [ $type, $target ];
}


###############################################################################
#
# _add_package_relationship()
#
# Add container relationship to XLSX .rels xml files.
#
sub _add_package_relationship {

    my $self   = shift;
    my $type   = shift;
    my $target = shift;

    $type   = $package_schema . $type;
    $target = $target . '.xml';

    push @{ $self->{_rels} }, [ $type, $target ];
}



###############################################################################
#
# _add_worksheet_relationship()
#
# Add worksheet relationship to sheet.rels xml files.
#
sub _add_worksheet_relationship {

    my $self        = shift;
    my $type        = shift;
    my $target      = shift;
    my $target_mode = shift;

    $type   = $document_schema . $type;
    $target = $target;

    push @{ $self->{_rels} }, [ $type, $target, $target_mode ];
}



###############################################################################
#
# Internal methods.
#
###############################################################################


###############################################################################
#
# XML writing methods.
#
###############################################################################


##############################################################################
#
# _write_relationships()
#
# Write the <Relationships> element.
#
sub _write_relationships {

    my $self = shift;

    my @attributes = ( 'xmlns' => $package_schema, );

    $self->{_writer}->startTag( 'Relationships', @attributes );

    for my $rel ( @{ $self->{_rels} } ) {
        $self->_write_relationship( @$rel );
    }

    $self->{_writer}->endTag( 'Relationships' );

    # Close the XM writer object and filehandle.
    $self->{_writer}->end();
    $self->{_writer}->getOutput()->close();
}


##############################################################################
#
# _write_relationship()
#
# Write the <Relationship> element.
#
sub _write_relationship {

    my $self        = shift;
    my $type        = shift;
    my $target      = shift;
    my $target_mode = shift;

    my @attributes = (
        'Id'     => 'rId' . $self->{_id}++,
        'Type'   => $type,
        'Target' => $target,
    );

    push @attributes, ( 'TargetMode' => $target_mode ) if $target_mode;

    $self->{_writer}->emptyTag( 'Relationship', @attributes );
}


1;


__END__

=pod

=head1 NAME

Relationships - A class for writing the Excel XLSX Rels file.

=head1 SYNOPSIS

See the documentation for L<Excel::Writer::XLSX>.

=head1 DESCRIPTION

This module is used in conjunction with L<Excel::Writer::XLSX>.

=head1 AUTHOR

John McNamara jmcnamara@cpan.org

=head1 COPYRIGHT

� MM-MMXI, John McNamara.

All Rights Reserved. This module is free software. It may be used, redistributed and/or modified under the same terms as Perl itself.

=head1 LICENSE

Either the Perl Artistic Licence L<http://dev.perl.org/licenses/artistic.html> or the GPL L<http://www.opensource.org/licenses/gpl-license.php>.

=head1 DISCLAIMER OF WARRANTY

See the documentation for L<Excel::Writer::XLSX>.

=cut
